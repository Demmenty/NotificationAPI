from drf_yasg.inspectors import SwaggerAutoSchema


class CustomAutoSchema(SwaggerAutoSchema):
    def get_link(self, path, method, base_url):
        link = super().get_link(path, method, base_url)
        link._fields += []
        return link
