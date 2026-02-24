class PresensiSelectors:
    NAME_INPUT = "#nama"
    UNIT_SELECT = "#unit"

    ACTION_BUTTONS = {
        "MASUK": "button.btn-masuk[onclick*=\"presensi('MASUK')\"]",
        "KELUAR": "button.btn-keluar[onclick*=\"presensi('KELUAR')\"]",
    }
