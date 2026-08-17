from __future__ import annotations

import streamlit as st
from services.identity_client import require_login
from components.bi.comercial_dashboard import render


def run():
    require_login()
    render()


if __name__ == "__main__":
    run()
