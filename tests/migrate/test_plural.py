# coding=utf8
from __future__ import unicode_literals

import unittest

import fluent.syntax.ast as FTL
try:
    from compare_locales.parser import PropertiesParser
except ImportError:
    PropertiesParser = None

from fluent.migrate.util import parse, ftl_message_to_json
from fluent.migrate.helpers import EXTERNAL_ARGUMENT
from fluent.migrate.transforms import evaluate, PLURALS, REPLACE_IN_TEXT


class MockContext(unittest.TestCase):
    maxDiff = None
    # Plural categories corresponding to English (en-US).
    plural_categories = ('one', 'other')

    def get_source(self, path, key):
        # Ignore path (test.properties) and get translations from self.strings
        # defined in setUp.
        return self.strings.get(key, None).val


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestPlural(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            deleteAll=Delete this download?;Delete all downloads?
        ''')

        self.message = FTL.Message(
            FTL.Identifier('delete-all'),
            value=PLURALS(
                'test.properties',
                'deleteAll',
                EXTERNAL_ARGUMENT('num')
            )
        )

    def test_plural(self):
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                        [one] Delete this download?
                       *[other] Delete all downloads?
                    }
            ''')
        )

    def test_plural_too_few_variants(self):
        self.plural_categories = ('one', 'few', 'many', 'other')
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                        [one] Delete this download?
                       *[few] Delete all downloads?
                    }
            ''')
        )

    def test_plural_too_many_variants(self):
        self.plural_categories = ('one',)
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                       *[one] Delete this download?
                    }
            ''')
        )


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestPluralLiteral(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            deleteAll=Delete this download?;Delete all downloads?
        ''')

        self.message = FTL.Message(
            FTL.Identifier('delete-all'),
            value=PLURALS(
                'test.properties',
                'deleteAll',
                EXTERNAL_ARGUMENT('num')
            )
        )

    def test_plural_literal(self):
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                        [one] Delete this download?
                       *[other] Delete all downloads?
                    }
            ''')
        )


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestPluralReplace(MockContext):
    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            deleteAll=Delete this download?;Delete #1 downloads?
        ''')

    def test_plural_replace(self):
        msg = FTL.Message(
            FTL.Identifier('delete-all'),
            value=PLURALS(
                'test.properties',
                'deleteAll',
                EXTERNAL_ARGUMENT('num'),
                lambda text: REPLACE_IN_TEXT(
                    text,
                    {
                        '#1': EXTERNAL_ARGUMENT('num')
                    }
                )
            )
        )

        self.assertEqual(
            evaluate(self, msg).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                        [one] Delete this download?
                       *[other] Delete { $num } downloads?
                    }
            ''')
        )


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestOneCategory(MockContext):
    # Plural categories corresponding to Turkish (tr).
    plural_categories = ('other',)

    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            deleteAll=#1 indirme silinsin mi?
        ''')

        self.message = FTL.Message(
            FTL.Identifier('delete-all'),
            value=PLURALS(
                'test.properties',
                'deleteAll',
                EXTERNAL_ARGUMENT('num'),
                lambda text: REPLACE_IN_TEXT(
                    text,
                    {
                        '#1': EXTERNAL_ARGUMENT('num')
                    }
                )
            )
        )

    def test_no_select_expression(self):
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all = { $num } indirme silinsin mi?
            ''')
        )


@unittest.skipUnless(PropertiesParser, 'compare-locales required')
class TestManyCategories(MockContext):
    # Plural categories corresponding to Polish (pl).
    plural_categories = ('one', 'few', 'many', 'other')

    def setUp(self):
        self.strings = parse(PropertiesParser, '''
            deleteAll=Usunąć plik?;Usunąć #1 pliki?;Usunąć #1 plików?
        ''')

        self.message = FTL.Message(
            FTL.Identifier('delete-all'),
            value=PLURALS(
                'test.properties',
                'deleteAll',
                EXTERNAL_ARGUMENT('num'),
                lambda text: REPLACE_IN_TEXT(
                    text,
                    {
                        '#1': EXTERNAL_ARGUMENT('num')
                    }
                )
            )
        )

    def test_too_few_variants(self):
        # StringBundle's plural rule #9 used for Polish has three categories
        # which is one fewer than the CLDR's. The migrated string will not have
        # the [other] variant and [many] will be marked as the default.
        self.assertEqual(
            evaluate(self, self.message).to_json(),
            ftl_message_to_json('''
                delete-all =
                    { $num ->
                        [one] Usunąć plik?
                        [few] Usunąć { $num } pliki?
                       *[many] Usunąć { $num } plików?
                    }
            ''')
        )


if __name__ == '__main__':
    unittest.main()