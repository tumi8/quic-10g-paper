import argparse
import logging
import os

import asyncio

from aioquic.asyncio import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.packet import QuicProtocolVersion
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.logger import QuicFileLogger
from aioquic.tls import CipherSuite


from http_protocol import HttpServerProtocol
from app import App

from helper import environ_or_required, mkdirs
from helper import Testcase

logger = logging.getLogger("server")


def main(args):

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

    # Set root for http application
    App.app_root = args.www

    configuration = QuicConfiguration(
        alpn_protocols=H3_ALPN,
        is_client=False,
        max_datagram_frame_size=65536,
        quic_logger=quic_logger,
        secrets_log_file=secrets_log_file,
        supported_versions=[QuicProtocolVersion.VERSION_1]
    )
    configuration.load_cert_chain(
        os.path.join(args.certs, 'cert.pem'),
        os.path.join(args.certs, 'priv.key'),
    )

    additional_args = {
        'retry': False
    }

    ticket_store = SessionTicketStore()

    if args.testcase == Testcase.HANDSHAKE:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.TRANSFER:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.VERSION_NEGOTIATION:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.MULTI_HANDSHAKE:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.CHACHA_20:
        configuration.cipher_suites = [CipherSuite.CHACHA20_POLY1305_SHA256]
    elif args.testcase == Testcase.TRANSPORT_PARAMETER:
        # Nothing to do here
        # TODO: set initial_max_streams_bidi <= 10
        pass
    elif args.testcase == Testcase.RETRY:
        additional_args['retry'] = True
    elif args.testcase == Testcase.RESUMPTION:
        additional_args['session_ticket_fetcher'] = ticket_store.pop
        additional_args['session_ticket_handler'] = ticket_store.add
    elif args.testcase == Testcase.ZERO_RTT:
        additional_args['session_ticket_fetcher'] = ticket_store.pop
        additional_args['session_ticket_handler'] = ticket_store.add
    elif args.testcase == Testcase.M_GOODPUT:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.M_QLOG:
        # Nothing to do here
        pass
    elif args.testcase == Testcase.M_OPTIMIZE:
        # Nothing to do here
        pass

    logger.info(f'Listening on {args.ip}:{args.port}')
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        serve(
            args.ip,
            args.port,
            configuration=configuration,
            #stream_handler=stream_handler,
            create_protocol=HttpServerProtocol,
            **additional_args,
        )
    )
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass


class SessionTicketStore:
    """
    Simple in-memory store for session tickets.
    """

    def __init__(self) -> None:
        self.tickets = {}

    def add(self, ticket) -> None:
        self.tickets[ticket.ticket] = ticket

    def pop(self, label) :
        return self.tickets.pop(label, None)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Server Application")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="increase logging verbosity"
    )
    parser.add_argument(
        "--ip", type=str,
        help="The IP the server should listen on",
        **environ_or_required('IP', default='localhost')
    )
    parser.add_argument(
        "--port", type=int,
        help="The IP the server should listen on",
        **environ_or_required('PORT', default=4433)
    )
    parser.add_argument(
        "--certs", type=str,
        help="The certs created to be used by the server during the handshake",
        **environ_or_required('CERTS')
    )
    parser.add_argument(
        "--testcase", type=str,
        help="The name of the testcase",
        **environ_or_required('TESTCASE')
    )
    parser.add_argument(
        "--www", type=str,
        help="The directory containing all files the server should be able to serve under /",
        **environ_or_required('WWW')
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
                os.path.join(args.logs, 'server.txt')
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

    main(args)
