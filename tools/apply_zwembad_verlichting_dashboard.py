#!/usr/bin/env python3
"""Build zwembadverlichting dashboard section for dashboard-thuis / zwembad tab."""

from home_verlichting_stack import SPOTS_SECONDARY, build_color_chips


def _press_action(entity_id: str) -> dict:
    return {
        "action": "perform-action",
        "perform_action": "button.press",
        "target": {"entity_id": entity_id},
    }


def _color_card(entity_id: str, color: str, label: str) -> dict:
    return {
        "type": "custom:mushroom-template-card",
        "layout": "vertical",
        "icon": "mdi:circle",
        "icon_color": color,
        "primary": label,
        "tap_action": _press_action(entity_id),
        "hold_action": {"action": "more-info", "entity": entity_id},
        "grid_options": {"columns": 2, "rows": 1, "min_columns": 1, "min_rows": 1},
    }


PROGRAM_ENTITY = "number.zwembad_verlichting_huidig_programma"
NEXT_ENTITY = "button.zwembad_verlichting_volgende_programma"
PREV_ENTITY = "button.zwembad_verlichting_vorig_programma"
LAMPEN_AAN = "binary_sensor.zwembad_verlichting_lampen_aan"
PROGRAM_BUSY = "binary_sensor.zwembad_verlichting_programma_bezig"
BLE_VERBONDEN = "binary_sensor.zwembad_verlichting_ble_verbonden"


def _gated_press_chips(
    *,
    icon: str,
    icon_color_on: str,
    entity_id: str,
    content: str = "",
) -> list[dict]:
    active = {
        "type": "template",
        "icon": icon,
        "icon_color": icon_color_on,
        "content": content,
        "tap_action": _press_action(entity_id),
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


def _prog_step_chips(*, icon: str, entity_id: str) -> list[dict]:
    """Prog +/- : lampen aan, BLE ok, niet bezig."""
    active = {
        "type": "template",
        "icon": icon,
        "icon_color": "blue",
        "content": "",
        "tap_action": _press_action(entity_id),
    }
    inactive = {
        "type": "template",
        "icon": icon,
        "icon_color": "disabled",
        "content": "",
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


def _program_control_chips() -> dict:
    """Prog - / teller / Prog + — lampen aan + 3s cooldown na elke stap."""
    display = {
        "type": "template",
        "entity": PROGRAM_ENTITY,
        "icon": "mdi:counter",
        "icon_color": "blue",
        "content": "Prog {{ states('number.zwembad_verlichting_huidig_programma') | int(0) }}",
        "tap_action": {"action": "more-info", "entity": PROGRAM_ENTITY},
    }
    return {
        "type": "custom:mushroom-chips-card",
        "alignment": "center",
        "chips": [
            *_prog_step_chips(icon="mdi:minus", entity_id=PREV_ENTITY),
            display,
            *_prog_step_chips(icon="mdi:plus", entity_id=NEXT_ENTITY),
        ],
    }


def _program_tile() -> dict:
    """Program display — large number as primary, label as secondary."""
    return {
        "type": "custom:mushroom-template-card",
        "entity": PROGRAM_ENTITY,
        "icon": "mdi:counter",
        "icon_color": "blue",
        "layout": "horizontal",
        "fill_container": True,
        "primary": "{{ states('number.zwembad_verlichting_huidig_programma') | int(0) }}",
        "secondary": "Prog",
        "tap_action": {"action": "more-info"},
        "entity_id": [PROGRAM_ENTITY],
    }


def _spots_tile(*, grid_options: dict | None = None) -> dict:
    """Tile-style card with inline toggle and program subtitle."""
    color_tpl = "{% if is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') %}amber{% else %}disabled{% endif %}"
    card = {
        "type": "custom:mushroom-template-card",
        "entity": "switch.zwembad_verlichting_zwembad_lampen",
        "icon": "mdi:light-recessed",
        "color": color_tpl,
        "icon_color": color_tpl,
        "layout": "horizontal",
        "fill_container": True,
        "primary": "Spots",
        "secondary": SPOTS_SECONDARY,
        "features": [{"type": "toggle"}],
        "features_position": "inline",
        "tap_action": {"action": "none"},
        "entity_id": [
            "switch.zwembad_verlichting_zwembad_lampen",
            "number.zwembad_verlichting_huidig_programma",
            "binary_sensor.zwembad_verlichting_ble_verbonden",
            "binary_sensor.zwembad_verlichting_lampen_aan",
            "binary_sensor.zwembad_verlichting_kleur_opslaan",
        ],
    }
    if grid_options:
        card["grid_options"] = grid_options
    return card


def _spots_card(*, grid_options: dict | None = None, tap_action: dict | None = None) -> dict:
    card = {
        "type": "custom:mushroom-template-card",
        "layout": "horizontal",
        "fill_container": True,
        "entity": "switch.zwembad_verlichting_zwembad_lampen",
        "icon": "mdi:light-recessed",
        "icon_color": "{% if is_state('binary_sensor.zwembad_verlichting_ble_verbonden', 'off') %}disabled{% elif is_state('binary_sensor.zwembad_verlichting_lampen_aan', 'on') %}amber{% else %}disabled{% endif %}",
        "primary": "Spots",
        "secondary": SPOTS_SECONDARY,
        "tap_action": tap_action or {"action": "toggle"},
        "entity_id": [
            "switch.zwembad_verlichting_zwembad_lampen",
            "number.zwembad_verlichting_huidig_programma",
            "binary_sensor.zwembad_verlichting_ble_verbonden",
            "binary_sensor.zwembad_verlichting_lampen_aan",
            "binary_sensor.zwembad_verlichting_kleur_opslaan",
        ],
    }
    if grid_options:
        card["grid_options"] = grid_options
    return card


def _lamp_tile() -> dict:
    return {
        "type": "tile",
        "entity": "switch.zwembad_verlichting_zwembad_lampen",
        "name": "Lampen",
        "icon": "mdi:light-recessed",
        "color": "amber",
        "features": [{"type": "toggle"}],
        "vertical": False,
    }


def _ble_tile() -> dict:
    """Standalone BLE tile — edit freely in the HA dashboard UI."""
    return {
        "type": "tile",
        "entity": "binary_sensor.zwembad_verlichting_ble_verbonden",
        "name": "BLE",
        "color": "primary",
    }


def _ble_prog_row() -> dict:
    """BLE and current program side by side (equal tiles)."""
    return {
        "type": "horizontal-stack",
        "cards": [_ble_tile(), _program_tile()],
    }


def build_verlichting_section() -> dict:
    return {
        "cards": [
            {
                "type": "heading",
                "heading": "Zwembadverlichting",
                "icon": "mdi:light-recessed",
            },
            _spots_tile(grid_options={"columns": 12, "rows": 2}),
            {
                "type": "vertical-stack",
                "cards": build_color_chips(include_lamp=False, show_numbers=True),
            },
            _ble_prog_row(),
        ]
    }


if __name__ == "__main__":
    import json

    print(json.dumps(build_verlichting_section(), indent=2))
