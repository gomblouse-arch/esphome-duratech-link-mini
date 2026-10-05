#!/usr/bin/env python3
"""Home overview Zwembad section: add verlichting stack with color chips."""

COLOR_BUTTONS = [
    ("button.zwembad_verlichting_1_kaarslicht", "1", "#FF9A3C"),
    ("button.zwembad_verlichting_2_warm_wit", "2", "#FFE8C8"),
    ("button.zwembad_verlichting_3_neutraal_wit", "3", "#F5F5F5"),
    ("button.zwembad_verlichting_4_koud_wit", "4", "#D6EEFF"),
    ("button.zwembad_verlichting_5_caribisch_blauw", "5", "#2DD4BF"),
    ("button.zwembad_verlichting_6_blauw", "6", "#2563EB"),
    ("button.zwembad_verlichting_7_groen", "7", "#22C55E"),
    ("button.zwembad_verlichting_8_rood", "8", "#EF4444"),
    ("button.zwembad_verlichting_9_paars", "9", "#A855F7"),
    ("button.zwembad_verlichting_10_geel_dynamisch", "10", "#FACC15"),
    ("button.zwembad_verlichting_11_blauw_dynamisch", "11", "#38BDF8"),
]

SPOTS_SECONDARY = (
    "{% if not is_state('binary_sensor.zwembad_verlichting_ble_verbonden', 'on') %}"
    "BLE weg"
    "{% else %}"
    "{% set p = states('number.zwembad_verlichting_huidig_programma') | int(0) %}"
    "{% set kleuren = {1: 'Kaarslicht', 2: 'Warm wit', 3: 'Neutraal wit', 4: 'Koud wit', "
    "5: 'Caribisch blauw', 6: 'Blauw', 7: 'Groen', 8: 'Rood', 9: 'Paars', "
    "10: 'Geel dynamisch', 11: 'Blauw dynamisch'} %}"
    "{% set kleur = kleuren.get(p, 'Onbekend') %}"
    "{% set status = 'Aan' if is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') else 'Uit' %}"
    "{% set settle = ' · wacht 30s' if is_state('binary_sensor.zwembad_verlichting_kleur_opslaan', 'on') and status == 'Uit' else '' %}"
    "{{ status ~ ' · ' ~ kleur ~ ' · ' ~ p ~ '/11' ~ settle }}"
    "{% endif %}"
)


LAMPEN_AAN = "binary_sensor.zwembad_verlichting_lampen_aan"
PROGRAM_BUSY = "binary_sensor.zwembad_verlichting_programma_bezig"
BLE_VERBONDEN = "binary_sensor.zwembad_verlichting_ble_verbonden"


def _press(entity_id: str) -> dict:
    return {
        "action": "perform-action",
        "perform_action": "button.press",
        "target": {"entity_id": entity_id},
    }


def _gated_press_chips(
    *,
    icon: str,
    icon_color_on: str,
    entity_id: str,
    content: str = "",
) -> list[dict]:
    """Show pressable chip when lights are on; disabled chip when off."""
    active = {
        "type": "template",
        "icon": icon,
        "icon_color": icon_color_on,
        "content": content,
        "tap_action": _press(entity_id),
    }
    inactive = {
        "type": "template",
        "icon": icon,
        "icon_color": "disabled",
        "content": content,
        "tap_action": {"action": "none"},
    }
    return [
        {
            "type": "conditional",
            "conditions": [{"entity": LAMPEN_AAN, "state": "on"}],
            "chip": active,
        },
        {
            "type": "conditional",
            "conditions": [{"entity": LAMPEN_AAN, "state": "off"}],
            "chip": inactive,
        },
    ]


def _cooldown_press_chips(
    *,
    icon: str,
    icon_color_on: str,
    entity_id: str,
    content: str = "",
) -> list[dict]:
    """Active only when lights on, BLE connected, and not busy.

    Four mutually exclusive conditionals so at most one chip shows.
    """
    active = {
        "type": "template",
        "icon": icon,
        "icon_color": icon_color_on,
        "content": content,
        "tap_action": _press(entity_id),
    }
    inactive = {
        "type": "template",
        "icon": icon,
        "icon_color": "disabled",
        "content": content,
        "tap_action": {"action": "none"},
    }
    return [
        {
            "type": "conditional",
            "conditions": [
                {"entity": LAMPEN_AAN, "state": "on"},
                {"entity": BLE_VERBONDEN, "state": "on"},
                {"entity": PROGRAM_BUSY, "state_not": "on"},
            ],
            "chip": active,
        },
        {
            "type": "conditional",
            "conditions": [{"entity": LAMPEN_AAN, "state": "off"}],
            "chip": inactive,
        },
        {
            "type": "conditional",
            "conditions": [
                {"entity": LAMPEN_AAN, "state": "on"},
                {"entity": BLE_VERBONDEN, "state_not": "on"},
            ],
            "chip": inactive,
        },
        {
            "type": "conditional",
            "conditions": [
                {"entity": LAMPEN_AAN, "state": "on"},
                {"entity": BLE_VERBONDEN, "state": "on"},
                {"entity": PROGRAM_BUSY, "state": "on"},
            ],
            "chip": inactive,
        },
    ]


def build_color_chips(*, include_lamp: bool = False, show_numbers: bool = False) -> list[dict]:
    color_chips: list[dict] = []
    for entity_id, label, color in COLOR_BUTTONS:
        color_chips.extend(
            _cooldown_press_chips(
                icon="mdi:circle",
                icon_color_on=color,
                entity_id=entity_id,
                content=label if show_numbers else "",
            )
        )

    volg_chip = _cooldown_press_chips(
        icon="mdi:skip-next",
        icon_color_on="blue",
        entity_id="button.zwembad_verlichting_volgende_programma",
    )

    # 4 conditional chips per kleur (aan+ble+vrij / uit / ble-weg / bezig)
    per = 4
    row1_colors = color_chips[: 6 * per]
    row2_colors = color_chips[6 * per :]

    row1 = row1_colors
    if include_lamp:
        lamp_chip = {
            "type": "template",
            "entity": "switch.zwembad_verlichting_zwembad_lampen",
            "content": "",
            "icon": "{% if is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') %}mdi:lightbulb{% else %}mdi:lightbulb-outline{% endif %}",
            "icon_color": "{% if is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') %}amber{% else %}disabled{% endif %}",
            "tap_action": {"action": "toggle"},
            "hold_action": {
                "action": "navigate",
                "navigation_path": "/dashboard-thuis/zwembad",
            },
        }
        row1 = [lamp_chip, *row1_colors]

    return [
        {
            "type": "custom:mushroom-chips-card",
            "alignment": "center",
            "chips": row1,
        },
        {
            "type": "custom:mushroom-chips-card",
            "alignment": "center",
            "chips": [*row2_colors, *volg_chip],
        },
    ]


def build_home_verlichting_stack() -> dict:
    chip_rows = build_color_chips(include_lamp=True)

    return {
        "type": "vertical-stack",
        "cards": [
            {
                "type": "custom:mushroom-template-card",
                "layout": "horizontal",
                "fill_container": True,
                "entity": "switch.zwembad_verlichting_zwembad_lampen",
                "icon": "mdi:light-recessed",
                "icon_color": "{% if is_state('binary_sensor.zwembad_verlichting_ble_verbonden', 'off') %}disabled{% elif is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') %}amber{% else %}disabled{% endif %}",
                "primary": "Spots",
                "secondary": SPOTS_SECONDARY,
                "tap_action": {"action": "none"},
                "hold_action": {
                    "action": "navigate",
                    "navigation_path": "/dashboard-thuis/zwembad",
                },
                "entity_id": [
                    "switch.zwembad_verlichting_zwembad_lampen",
                    "number.zwembad_verlichting_huidig_programma",
                    "binary_sensor.zwembad_verlichting_ble_verbonden",
                    "binary_sensor.zwembad_verlichting_lampen_aan",
                    "binary_sensor.zwembad_verlichting_kleur_opslaan",
                ],
            },
            *chip_rows,
        ],
        "grid_options": {"columns": 12, "rows": 3, "min_columns": 6, "min_rows": 2},
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_home_verlichting_stack(), indent=2))
