import argparse
import logging
import os
import ssl
import time

from helper import environ_or_required, mkdirs
from helper import Testcase, URL
from typing import cast

from http_protocol import HttpClient, perform_http_request

import asyncio

from aioquic.asyncio import connect
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.packet import QuicProtocolVersion
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.logger import QuicFileLogger
from aioquic.tls import CipherSuite

logger = logging.getLogger("client")


async def main(args):

    if args.qlog:
        mkdirs(args.qlog)
        quic_logger = QuicFileLogger(args.qlog)
    else:
        quic_logger = None

    if args.keylog:
        mkdirs(args.keylog)
        secrets_log_file = open(args.keylog, "a")
    else:
        secrets_log_file = None

    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN,
        is_client=True,
        max_datagram_frame_size=65536,
        quic_logger=quic_logger,
        secrets_log_file=secrets_log_file,
        verify_mode=ssl.CERT_NONE,
        supported_versions=[QuicProtocolVersion.VERSION_1]
    )

    if len(args.requests) == 0:
        logger.debug('Nothing to request ...')
        return

    args.requests = [URL.from_string(request) for request in args.requests]
    host = args.requests[0].hostname
    port = args.requests[0].port

    session_ticket = None

    def get_session_ticket(ticket):
        nonlocal session_ticket
        session_ticket = ticket

    if host is None or port is None:
        logger.debug(f'Unknown host/port from {args.requests[0].geturl()}')
        return

    logger.debug(f'Connecting to {host}:{port} ...')

    if args.testcase == Testcase.HANDSHAKE:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.TRANSFER:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.VERSION_NEGOTIATION:
        configuration.supported_versions = [QuicProtocolVersion.DRAFT_29, QuicProtocolVersion.VERSION_1]
    elif args.testcase == Testcase.MULTI_HANDSHAKE:
        for request in args.requests:
            await run_requests(host, port, configuration, args.downloads, [request])
        return
    elif args.testcase == Testcase.CHACHA_20:
        configuration.cipher_suites = [CipherSuite.CHACHA20_POLY1305_SHA256]
    elif args.testcase == Testcase.TRANSPORT_PARAMETER:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.RETRY:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.RESUMPTION:
        connect_parameters = {'session_ticket_handler': get_session_ticket}
        await run_requests(host, port, configuration, args.downloads, args.requests[:1],
                           connect_parameters=connect_parameters, wait=10)

        configuration.session_ticket = session_ticket
        await run_requests(host, port, configuration, args.downloads, args.requests[1:])
        return
    elif args.testcase == Testcase.ZERO_RTT:
        connect_parameters = {'session_ticket_handler': get_session_ticket}
        await run_requests(host, port, configuration, args.downloads, args.requests[:1],
                           connect_parameters=connect_parameters, wait=10)

        configuration.session_ticket = session_ticket
        await run_requests(host, port, configuration, args.downloads, args.requests[1:], zero_rtt=True)
        return
    elif args.testcase == Testcase.M_GOODPUT:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.M_QLOG:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.M_OPTIMIZE:
        # Nothing to do here
        pass

    await run_requests(host, port, configuration, args.downloads, args.requests)


async def run_requests(host, port, configuration, download, requests,
                       zero_rtt=False, connect_parameters={}, wait=0):
    async with connect(
            host,
            port,
            configuration=configuration,
            create_protocol=HttpClient,
            # session_ticket_handler=save_session_ticket,
            # local_port=local_port,
            wait_connected=not zero_rtt,
            **connect_parameters
    ) as client:

        coros = [
            perform_http_request(
                client=client,
                url=url.geturl(),
                data=None,
                include=False,
                output_dir=download,
            )
            for url in requests
        ]
        await asyncio.gather(*coros)
        await asyncio.sleep(wait)
        client.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Client Application")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase logging verbosity"
    )
    parser.add_argument(
        "--requests", nargs='+',
        help="A list of requests a client should execute one by one. (e.g., https://127.0.0.2:445/xyz ...)",
        **environ_or_required('REQUESTS', default=[])
    )
    parser.add_argument(
        "--testcase", type=str,
        help="The name of the testcase",
        **environ_or_required('TESTCASE')
    )
    parser.add_argument(
        "--downloads", type=str,
        help="The directory were files should be saved to. They are compared to the original files served by the server to verify tests",
        **environ_or_required('DOWNLOADS')
    )
    parser.add_argument(
        "--logs", type=str,
        help="The directory name to write general logs to",
        **environ_or_required('LOGS', required=False)
    )
    parser.add_argument(
        "--qlog", type=str,
        help="qlog results are not required but might help to debug your output. However they have a negativ impact on performance so you might want to deactivate it for some tests",
        **environ_or_required('QLOGDIR', required=False)
    )
    parser.add_argument(
        "--keylog", type=str,
        help="The variable contains the path + name of the keylog file. The output is required to decrypt traces and verify tests",
        **environ_or_required('SSLKEYLOGFILE', required=False)
    )

    args = parser.parse_args()

    log_handlers = [logging.StreamHandler()]
    if args.logs:
        if not os.path.exists(args.logs):
            os.makedirs(args.logs)
        log_handlers.append(
            logging.FileHandler(
                os.path.join(args.logs, 'client.txt')
            )
        )

    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
        handlers=log_handlers
    )

    # Parse handshake
    try:
        args.testcase = Testcase.from_string(args.testcase)
    except ValueError:
        logger.error(f'Unknown testcase: {args.testcase}')
        exit(127)

    if args.requests is None:
        args.requests = []

    if type(args.requests) is not list:
        args.requests = args.requests.split(' ')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(
       main(args)
    )