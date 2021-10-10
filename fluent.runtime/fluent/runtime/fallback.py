import codecs
import os
import redis


class FluentLocalization:
    """
    Generic API for Fluent applications.

    This handles language fallback, bundle creation and string localization.
    It uses the given resource loader to load and parse Fluent data.
    """
    def __init__(
        self, locales, resource_ids, resource_loader,
        use_isolating=False,
        bundle_class=None, functions=None,
    ):
        self.locales = locales
        self.resource_ids = resource_ids
        self.resource_loader = resource_loader
        self.use_isolating = use_isolating
        if bundle_class is None:
            from fluent.runtime import FluentBundle
            self.bundle_class = FluentBundle
        else:
            self.bundle_class = bundle_class
        self.functions = functions
        self._bundle_cache = []
        self._bundle_it = self._iterate_bundles()

    def format_value(self, msg_id, args=None):
        for bundle in self._bundles():
            if not bundle.has_message(msg_id):
                continue
            msg = bundle.get_message(msg_id)
            if not msg.value:
                continue
            val, errors = bundle.format_pattern(msg.value, args)
            return val
        return msg_id

    def _create_bundle(self, locales):
        return self.bundle_class(
            locales, functions=self.functions, use_isolating=self.use_isolating
        )

    def _bundles(self):
        bundle_pointer = 0
        while True:
            if bundle_pointer == len(self._bundle_cache):
                try:
                    self._bundle_cache.append(next(self._bundle_it))
                except StopIteration:
                    return
            yield self._bundle_cache[bundle_pointer]
            bundle_pointer += 1

    def _iterate_bundles(self):
        for first_loc in range(0, len(self.locales)):
            locs = self.locales[first_loc:]
            for resources in self.resource_loader.resources(locs[0], self.resource_ids):
                bundle = self._create_bundle(locs)
                for resource in resources:
                    bundle.add_resource(resource)
                yield bundle


class AbstractResourceLoader:
    """
    Interface to implement for resource loaders.
    """
    def resources(self, locale, resource_ids):
        """
        Yield lists of FluentResource objects, corresponding to
        each of the resource_ids.
        If there are multiple locations, this may yield multiple lists.
        If a resource isn't found in any location, yield a partial list,
        but don't yield empty lists.
        """
        raise NotImplementedError


class FluentResourceLoader(AbstractResourceLoader):
    """
    Resource loader to read Fluent files from disk.

    Different locales are in different locations based on locale code.
    The locale code should be encoded as `{locale}` in the roots, or in
    the resource_ids.
    This loader does not support loading resources for one bundle from
    different roots.
    """
    def __init__(self, roots):
        """
        Create a resource loader. The roots may be a string for a single
        location on disk, or a list of strings.
        """
        self.roots = [roots] if isinstance(roots, str) else roots
        from fluent.runtime import FluentResource
        self.Resource = FluentResource
        self.load_env_vars()
        if self.in_memory is True:
            self.load_in_memnory_env_vars()
            self.redis_client = redis.client.Redis(
                host=self.REDIS_HOST, port=self.REDIS_PORT, db=self.TRANSLATION_REDIS_DB
            )

    def resources(self, locale, resource_ids):
        if self.in_memory is True:
            resources = []
            for resource_id in resource_ids:
                content = self.get_translation_file(resource_id)
                resources.append(self.Resource(content))
            if resources:
                yield resources
        else:
            for root in self.roots:
                resources = []
                for resource_id in resource_ids:
                    path = self.localize_path(os.path.join(root, resource_id), locale)
                    if not os.path.isfile(path):
                        continue
                    content = codecs.open(path, 'r', 'utf-8').read()
                    resources.append(self.Resource(content))
                if resources:
                    yield resources

    def localize_path(self, path, locale):
        return path.format(locale=locale)

    def load_env_vars(self):
        self.DI_LANG = os.environ['DI_LANG']
        self.in_memory = bool(os.environ['TRANSLATION_IN_MEMORY_MODE'])
        self.TRANSLATION_STATIC_FILES_PATH = os.environ.GET('TRANSLATION_STATIC_FILES_PATH')

    def load_in_memnory_env_vars(self):
        self.REDIS_HOST = os.environ['REDIS_HOST']
        self.REDIS_PORT = os.environ['REDIS_PORT']
        self.TRANSLATION_REDIS_DB = os.environ['TRANSLATION_REDIS_DB']
        self.TRANSLATION_REDIS_KEY = os.environ['TRANSLATION_REDIS_KEY']
        self.TRANSLATION_REDIS_TTL_IN_SECONDS = os.environ['TRANSLATION_REDIS_TTL_IN_SECONDS']

    def get_translation_file(self, file_name: str) -> str:
        """
        Get translation file by name, check if the translation data store in Redis, in case not - download the
        data from Google Cloud and store it in Redis with TTL
        :param file_name:  translation file name
        :return: translation data
        """
        if self.in_memory is True:
            file_key = self.TRANSLATION_REDIS_KEY.format(di_lang=self.DI_LANG, file_name=file_name)
            data = self.redis_client.get(file_key)
            if data is None:
                data = self.get_translation_file_from_cloud(file_name)
                if data:
                    # Save new data from cloud storage for caching future requests
                    self.redis_client.set(
                        self.TRANSLATION_REDIS_KEY.format(di_lang=self.DI_LANG, file_name=file_name),
                        data,
                        ex=self.TRANSLATION_REDIS_TTL_IN_SECONDS,
                    )

        else:
            data = self.get_translation_file_from_cloud(file_name)

        return data.decode() if isinstance(data, bytes) else data

    def get_translation_file_from_cloud(self, file_name: str) -> str:
        """
        Get translation file from cloud (currently work with Google Cloud)
        :param file_name:  translation file name
        :return: translation data
        """
        with open(
            f'{self.TRANSLATION_STATIC_FILES_PATH}/{self.DI_LANG}/{file_name}', mode="r", encoding="utf-8"
        ) as ftl_file:
            return ftl_file.read()
