from shop_core.customization.services import (
    clean_customizer_rule,
    customizer_url,
    set_number_format,
)


def test_customizer_url_rejects_javascript():
    assert customizer_url(
        "javascript:alert(1)"
    ) == ""


def test_customizer_rule_filters_unknown_style():
    rule = clean_customizer_rule({
        "id": "hero-title",
        "styles": {
            "color": "#AABBCC",
            "position": "fixed",
        },
    })

    assert rule["styles"] == {
        "color": "#AABBCC"
    }


class _Site:
    number_format = "persian"

    def save(self, update_fields):
        self.update_fields = update_fields


def test_set_number_format():
    site = _Site()
    set_number_format(
        site,
        "english",
    )
    assert site.number_format == "english"
    assert "updated_at" in site.update_fields
