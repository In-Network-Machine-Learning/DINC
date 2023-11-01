/*
 *
 * P4_16 for Tofino ASIC
 * Written Jan-Feb 2021 for pint
 *
 */
#include <core.p4>
#include <tna.p4>

#include "/root/bf-sde-9.2.0/pkgsrc/p4-examples/p4_16_programs/common/util.p4"

#define ETHERTYPE_IPV4 0x0800
#define ETHERTYPE_pint 0x1337

#define FLOW_ID_BITS 16
#define CHECKSUM_VERSION_BITS 8
#define CHECKSUM_INDEX_BITS 32 //should be at least FLOW_ID_BITS+CHECKSUM_VERSION_BITS

/*
 * Specify data types
 */
typedef bit<8> switch_id_t;
typedef bit<32> pint_digest_t;
typedef bit<16> decider_hash_t;
typedef bit<16> global_hash_t;
typedef bit<32> value_hash_t;
typedef bit<16> raw_value_t;
typedef bit<8> hop_number_t;

/*
 * Threshold (probability) to do baseline processing of digest (instead of XOR)
 * 32bit: 4294967296
 * 50%: 2147483648
 * 10%: 429496729
 *
 * 16bit: 65536
 * 50%: 32768
 * 10%: 6553
 */
 //Must be kept as power of 2, to keep complexity low
#define THRESHOLD_STATIC_PER_FLOW_TYPE 32768
#define THRESHOLD_XOR_MODIFY 8192

//If this is defined, a pint digest will always be sent to the CPU. Useful for following processing across path
#define ALWAYS_SEND_DIGEST

header ethernet_h
{
	bit<48> dstAddr;
	bit<48> srcAddr;
	bit<16> etherType;
}

header pint_h
{
	pint_digest_t digest;
    bit<16> etherType;
}

header ipv4_h
{
	bit<4> version;
	bit<4> ihl;
	bit<6> dscp;
	bit<2> ecn;
	bit<16> totalLen;
	bit<16> identification;
	bit<3> flags;
	bit<13> fragOffset;
	bit<8> ttl;
	bit<8> protocol;
	bit<16> hdrChecksum;
	bit<32> srcAddr;
	bit<32> dstAddr;
}

struct headers
{
	ethernet_h ethernet;
	pint_h pint;
	ipv4_h ipv4;
}

struct pint_cpu_digest_t
{
	pint_digest_t digest;
	hop_number_t hop_number;
	bit<16> pkt_id;
	bit<32> ip_src;
	bit<32> ip_dst;
	/*DEBUG DATA*/
	raw_value_t raw_value;
	/*END OF DEBUG DATA*/
}


struct ingress_metadata_t
{
	bit<1> is_sink;
	bit<1> send_pint_cpu_digest;

	hop_number_t hop_number;

	raw_value_t raw_value; //The raw value to encode into the digest
	decider_hash_t decider_hash;
	global_hash_t global_hash;
	value_hash_t value_hash;

	switch_id_t switch_id;
	global_hash_t threshold_baseline_modify;

	//Flagging how to process the digest
	bit<1> static_per_flow_doBaseline;
	bit<1> static_per_flow_doXOR;
}

struct egress_metadata_t
{

}

parser SwitchIngressParser(packet_in pkt, out headers hdr, out ingress_metadata_t ig_md, out ingress_intrinsic_metadata_t ig_intr_md)
{
	TofinoIngressParser() tofino_parser;

	state start
	{
		tofino_parser.apply(pkt, ig_intr_md);
		transition parse_ethernet;
	}

	state parse_ethernet
	{
		pkt.extract(hdr.ethernet);
		transition select(hdr.ethernet.etherType)
		{
			ETHERTYPE_IPV4: parse_ipv4;
			ETHERTYPE_pint: parse_pint;
			default: accept;
		}
	}

	state parse_pint
	{
		pkt.extract(hdr.pint);
		transition select(hdr.pint.etherType)
		{
			ETHERTYPE_IPV4: parse_ipv4;
			default: accept;
		}
	}

	state parse_ipv4
	{
		pkt.extract(hdr.ipv4);
		transition accept;
	}
}


control ControlPINT(inout headers hdr, inout ingress_metadata_t ig_md, in ingress_intrinsic_metadata_t ig_intr_md, in ingress_intrinsic_metadata_from_parser_t ig_intr_prsr_md, inout ingress_intrinsic_metadata_for_deparser_t ig_intr_dprsr_md, inout ingress_intrinsic_metadata_for_tm_t ig_intr_tm_md)
{
	Hash<decider_hash_t>(HashAlgorithm_t.CRC32) decider_hash;

	// dependency marker @!slice, 0!@  @!position, control!@
	/*
	 * Lookup table for the value encoding hash
	 * raw_value&pktID -> hash
	 */
	action doLookupHash_value(bit<32> hashValue)
	{
		ig_md.value_hash = hashValue;
	}
	table hashlookup_value
	{
		key = {
			ig_md.raw_value: exact;
			hdr.ipv4.identification: exact;
		}
		actions = {
			doLookupHash_value;
			@defaultonly NoAction;
		}
		size = 100000; //Example: 1000 pktID and 256 values -> 256k entries
		const default_action = NoAction;
	}
	// dependency marker @!end,0!@

	// dependency marker @!slice, 1!@  @!position, control!@
	/*
	 * Lookup table for the global hash
	 * hop_number&pktID -> hash
	 */
	action doLookupHash_global(global_hash_t hashValue)
	{
		ig_md.global_hash = hashValue;
	}
	table hashlookup_global
	{
		key = {
			ig_md.hop_number: exact;
			hdr.ipv4.identification: exact;
		}
		actions = {
			doLookupHash_global;
			@defaultonly NoAction;
		}
		size = 100000; //Example: 60k pktID and 9 diffs -> 540k entries
		const default_action = NoAction;
	}
	// dependency marker @!end,1!@

	// dependency marker @!slice, 2!@  @!position, control!@
	/*
	 * Check baseline writing probabilities
	 * Comparing global hash against hop-specific threshold to see if it should write into the baseline-processed digest
	 */
	action set_should_write_baseline()
	{
		ig_md.static_per_flow_doBaseline = 1;
	}
	table tbl_check_baseline_probability
	{
		key = {
			ig_md.hop_number: exact;
			ig_md.global_hash: lpm;
		}
		actions = {
			set_should_write_baseline;
			@defaultonly NoAction;
		}
		const default_action = NoAction;
		/*const entries = {
			(1, 0 .. 65535):  set_should_write_baseline();
			(2, 0 .. 32767):  set_should_write_baseline();
			(3, 0 .. 21844):  set_should_write_baseline();
			(4, 0 .. 16383):  set_should_write_baseline();
			(5, 0 .. 13106):  set_should_write_baseline();
			(6, 0 .. 10921):  set_should_write_baseline();
			(7, 0 .. 9361):  set_should_write_baseline();
			(8, 0 .. 8191):  set_should_write_baseline();
			(9, 0 .. 7280):  set_should_write_baseline();
			(10, 0 .. 6562):  set_should_write_baseline();
		} */
		size=16;
	}
	// dependency marker @!end,2!@

	// dependency marker @!slice, 3!@  @!previous, 2!@ @!position, control!@
	// resource marker @!stage, 5!@ @!memory, 5!@
    // p4 marker @!metadata_in!@
    // p4 marker @!metadata_out!@
	/*
	 * This table will map pre-calculated conditionals to digest-processing actions
	 */
	action static_per_flow_baseline()
	{
		hdr.pint.digest = ig_md.value_hash; //Just replace the digest
	}
	action static_per_flow_xor()
	{
		hdr.pint.digest = hdr.pint.digest^ig_md.value_hash; //XOR into the digest
	}
	table tbl_doProcessDigest
	{
		key = {
			ig_md.static_per_flow_doBaseline: exact;
			ig_md.static_per_flow_doXOR: exact;
		}
		actions = {
			static_per_flow_baseline;
			static_per_flow_xor;
			@defaultonly NoAction;
		}
		default_action = NoAction;
		const entries = {
			(1,0): static_per_flow_baseline();
			(0,1): static_per_flow_xor();
		}
		size=16;
	}
	// dependency marker @!end,3!@


	apply
	{
		// dependency marker @!slice, 0!@ @!previous, none!@ @!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in!@
        // p4 marker @!metadata_out!@

		//Set the value we want to encode (which in this case is the switch ID)
		ig_md.raw_value = (raw_value_t)ig_md.switch_id;

		//Prepare hashes
		ig_md.decider_hash = decider_hash.get({hdr.ipv4.identification}); //Calculate the decider hash
		hashlookup_global.apply(); //Lookup global hash from table (ig_md.global_hash)
		hashlookup_value.apply(); //Lookup value hash from table (ig_md.value_hash)

		// dependency marker @!end,0!@

        // dependency marker @!slice,1!@ @!previous,0!@ @!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in!@
        // p4 marker @!metadata_out!@

		/*
		 * Pre-calculate conditionals for PINT (for static per-flow telemetry)
		 */
		if(ig_md.decider_hash < THRESHOLD_STATIC_PER_FLOW_TYPE) //Baseline processing
		{
			tbl_check_baseline_probability.apply(); //Perform additional conditional through M/A table
		}
		else //XOR processing
		{
			if(ig_md.global_hash < THRESHOLD_XOR_MODIFY) //If this node should modify XOR digest (fixed probability)
			{
				ig_md.static_per_flow_doXOR = 1; //The XOR digest will be modified
			}
		}
		// dependency marker @!end,1!@

        // dependency marker @!slice,2!@ @!previous,0,1!@ @!position, control-apply!@
        // resource marker @!stage, 5!@ @!memory, 5!@
        // p4 marker @!metadata_in!@
        // p4 marker @!metadata_out!@

		//Calculate and write the digest to the packet
		tbl_doProcessDigest.apply();
		// dependency marker @!end,2!@
	}
}

control SwitchIngress(inout headers hdr, inout ingress_metadata_t ig_md, in ingress_intrinsic_metadata_t ig_intr_md, in ingress_intrinsic_metadata_from_parser_t ig_intr_prsr_md, inout ingress_intrinsic_metadata_for_deparser_t ig_intr_dprsr_md, inout ingress_intrinsic_metadata_for_tm_t ig_intr_tm_md)
{
	ControlPINT() pint;

	/*
	 * These are only required for emulating multiple hops on a single switch
	 */
	action set_switch_id(switch_id_t switch_id)
	{
		ig_md.switch_id = switch_id;
	}
	table tbl_set_switch_id
	{
		key = {
			ig_intr_md.ingress_port: exact;
		}
		actions = {
			set_switch_id;
			@defaultonly NoAction;
		}
		const default_action = NoAction;
	}

	action forward(PortId_t port)
	{
		ig_intr_tm_md.ucast_egress_port = port; //Set egress port
		hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
	}
	action drop()
	{
		ig_intr_dprsr_md.drop_ctl = 1;
	}
	table tbl_forward
	{
		key = {
			ig_md.switch_id: exact;
			hdr.ipv4.dstAddr: exact;
		}
		actions = {
			forward;
			@defaultonly drop;
		}
		default_action = drop;
	}

	/*
	 * Detect if sink, based on egress port
	 */
	action set_is_sink()
	{
		ig_md.is_sink = 1;
	}
	table tbl_checkIsSink
	{
		key = {
			ig_intr_tm_md.ucast_egress_port: exact;
		}
		actions = {
			set_is_sink;
			@defaultonly NoAction;
		}
		size = 128;
		const default_action = NoAction;
	}

	action add_pint_header()
	{
		hdr.pint.setValid();
		hdr.pint.etherType = hdr.ethernet.etherType;
		hdr.ethernet.etherType = ETHERTYPE_pint;
	}
	action remove_pint_header()
	{
		hdr.ethernet.etherType = hdr.pint.etherType;
		hdr.pint.setInvalid();
	}

	apply
	{
		//Initialize metadata
		ig_md.is_sink = 0;
		ig_md.send_pint_cpu_digest = 0;

		tbl_set_switch_id.apply();
		tbl_forward.apply();
		tbl_checkIsSink.apply();

		if(hdr.ipv4.isValid())
		{
			//If this is the source node
			if(!hdr.pint.isValid())
			{
				add_pint_header(); //Add the pint header
			}

			ig_md.hop_number = (bit<8>)(255 - hdr.ipv4.ttl); //Calculate the hop number

			//Run PINT on the packet
			pint.apply(hdr, ig_md, ig_intr_md, ig_intr_prsr_md, ig_intr_dprsr_md, ig_intr_tm_md);

			/*
			 * Check if sink
			 */
			if( ig_md.is_sink == 1)
			{
				//Remove the pint header
				remove_pint_header();

				//Flag that P4 digest should be sent
				ig_md.send_pint_cpu_digest = 1;
			}

			#IFDEF ALWAYS_SEND_DIGEST
			ig_md.send_pint_cpu_digest = 1;
			#ENDIF
		}
	}
}

control SwitchIngressDeparser(packet_out pkt, inout headers hdr, in ingress_metadata_t ig_md, in ingress_intrinsic_metadata_for_deparser_t ig_intr_dprsr_md)
{
	Digest<pint_cpu_digest_t>() pint_cpu_digest;


	apply
	{
		//Compile pint digest and send it to the Tofino CPU
		if( ig_md.send_pint_cpu_digest == 1 )
			pint_cpu_digest.pack({
				hdr.pint.digest,
				ig_md.hop_number,
				hdr.ipv4.identification,
				hdr.ipv4.srcAddr,
				hdr.ipv4.dstAddr
				/*DEBUG DATA*/
				,
				ig_md.raw_value
				/*END OF DEBUG DATA*/
			});

		pkt.emit(hdr.ethernet);
		pkt.emit(hdr.pint);
		pkt.emit(hdr.ipv4);
	}
}

parser SwitchEgressParser(packet_in pkt, out headers hdr, out egress_metadata_t eg_md, out egress_intrinsic_metadata_t eg_intr_md)
{
	TofinoEgressParser() tofino_parser;

	state start
	{
		tofino_parser.apply(pkt, eg_intr_md);
		transition accept;
	}
}

control SwitchEgress(inout headers hdr, inout egress_metadata_t eg_md, in egress_intrinsic_metadata_t eg_intr_md, in egress_intrinsic_metadata_from_parser_t eg_intr_from_prsr, inout egress_intrinsic_metadata_for_deparser_t eg_intr_md_for_dprsr, inout egress_intrinsic_metadata_for_output_port_t eg_intr_md_for_oport)
{
	apply
	{

	}
}

control SwitchEgressDeparser(packet_out pkt, inout headers hdr, in egress_metadata_t eg_md, in egress_intrinsic_metadata_for_deparser_t eg_dprsr_md)
{
	apply
	{
		pkt.emit(hdr);
	}
}


Pipeline(SwitchIngressParser(),
	SwitchIngress(),
	SwitchIngressDeparser(),
	SwitchEgressParser(),
	SwitchEgress(),
	SwitchEgressDeparser()
) pipe;

Switch(pipe) main;
