"""
Tornado Output Transforming Classes

"""
from tornado import web


class StripBlankLines(web.OutputTransform):

    def transform_first_chunk(self, status_code, headers, chunk, finishing):
        content_type = headers.get("Content-Type", "").split(";")[0]
        if content_type.split('/')[0] == 'text':
            chunk = self.transform_chunk(chunk, finishing)
            if "Content-Length" in headers:
                headers["Content-Length"] = str(len(chunk))
        return status_code, headers, chunk

    def transform_chunk(self, chunk, finishing):
        return '\n'.join([line for line in chunk.split('\n') if line])
