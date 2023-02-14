LSQUIC Implementation for the QUIC Interop Runner
=================================================

## Installation

## Usage

## Notes

* The lsquic http_server does not require the client to send a leading slash in the requested path. However, most other Implementations do so. The interoperability of the lsquic client with other servers was fixed in commit `6d72e7b7e5117a626015ed1def2ce8cb4569bac5`.
* Some lsquic engine settings that are controllable via the `-o` flag were changed by default. See the *Engine Settings* Section for more Information.

## Engine Settings

* CC_ALGO
    * Congestion control algorithm to use
    * Possible Values
        * 0: lsquic default
        * 1: Cubic (currently our default)
        * 2: BBRv1
        * 3: Adaptive (Cubic or BBRv1)
    * Changed default to CUBIC due to significantly worse performance of BBR
* DELAYED_ACKS
    * Turns on/off delayed ACKs extension
    * Possible Values
        * 0: off
        * 1: on (currently lsquic's and our default)
    * Integrated to evaluate performance differences
* IDLE_TIMEOUT
    * Idle connection timeout in seconds
    * Maximum value: 600
    * Default: 30
* MAX_UDP_PAYLOAD
    * Maximum packet size in bytes that the endpoint is willing to receive (does not get enforced by lsquic)
    * Default: 0 (no limit)
* INITIAL_MAX_DATA
    * Initial value for the maximum amount of data that can be sent on the connection in bytes.
    * Default for client: 15728640
    * Default for server: 1572864
* INITIAL_MAX_STREAM_DATA_BIDI_LOCAL
    * Initial flow control limit (in bytes) for locally initiated bidirectional streams.  This limit applies to newly created bidirectional streams opened by the endpoint that sends the transport parameter.
    * Default for client: 6291456
    * Default for server: 0
* INITIAL_MAX_STREAM_DATA_BIDI_REMOTE
    * Initial flow control limit for peer-initiated bidirectional streams.  This limit applies to newly created bidirectional streams opened by the endpoint that receives the transport parameter.
    * Default for client: 0
    * Default for server: 1048576
* INITIAL_MAX_STREAM_DATA_UNI
    * Initial flow control limit for unidirectional streams.  This limit applies to newly created unidirectional streams opened by the endpoint that receives the transport parameter.
    * Default for client: 32768
    * Default for server: 12288
* INITIAL_MAX_STREAMS_BIDI
    * Maximum initial number of bidirectional streams that the endpoint that receives this transport parameter is permitted to initiate.
    * Default: 100
* INITIAL_MAX_STREAMS_UNI
    * Maximum initial number of unidirectional streams that the endpoint that receives this transport parameter is permitted to initiate.
    * Default for client: 100
    * Default for server: 3
