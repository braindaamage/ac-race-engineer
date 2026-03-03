"""Unit tests for sanitize module."""
from sanitize import sanitize_name


class TestSanitizeName:
    def test_lowercase_conversion(self):
        assert sanitize_name("Ferrari488GT3") == "ferrari488gt3"

    def test_space_to_underscore(self):
        assert sanitize_name("my car name") == "my_car_name"

    def test_special_char_to_underscore(self):
        assert sanitize_name("car@v2.0!") == "car_v2_0"

    def test_consecutive_underscore_collapse(self):
        assert sanitize_name("car___name") == "car_name"

    def test_leading_trailing_underscore_strip(self):
        assert sanitize_name("_car_name_") == "car_name"

    def test_empty_string(self):
        assert sanitize_name("") == ""

    def test_already_clean_name(self):
        assert sanitize_name("ks_ferrari_488_gt3") == "ks_ferrari_488_gt3"

    def test_unicode_characters(self):
        result = sanitize_name("Nürburgring")
        assert result == "n_rburgring"
        # All chars should be [a-z0-9_]
        import re
        assert re.match(r"^[a-z0-9_]*$", result)

    def test_mixed_special_and_spaces(self):
        assert sanitize_name("My Car (v2.0)") == "my_car_v2_0"

    def test_only_special_chars(self):
        assert sanitize_name("@#$%") == ""

    def test_hyphens_replaced(self):
        assert sanitize_name("ks-ferrari-488") == "ks_ferrari_488"

    def test_unicode_produces_valid_ascii(self):
        """T038: Unicode names produce valid ASCII filenames."""
        import re
        result = sanitize_name("日本語テスト")
        assert re.match(r"^[a-z0-9_]*$", result) or result == ""

    def test_numbers_preserved(self):
        assert sanitize_name("car123") == "car123"
