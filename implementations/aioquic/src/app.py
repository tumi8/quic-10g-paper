import logging
import os

from starlette.applications import Starlette
from starlette.routing import Route
from starlette.endpoints import HTTPEndpoint
from starlette.responses import FileResponse, PlainTextResponse

logger = logging.getLogger("app")


class Index(HTTPEndpoint):
    async def get(self, request):
        return PlainTextResponse(f"Please specify a filename.")


class Files(HTTPEndpoint):

    async def get(self, request):
        filename = request.path_params['filename']
        logger.debug(f'Requested file {filename}')
        path = os.path.join(App.app_root, filename)
        if not os.path.exists(path):
            logger.debug(f'File {filename} not found.')
            return PlainTextResponse(f"File {filename} does not exist.", status_code=404)
        return FileResponse(path)


class App:

    app_root = '.'

    def __init__(self):
        routes = [
            Route("/", Index),
            Route("/{filename}", Files)
        ]
        self.app = Starlette(debug=True, routes=routes)


