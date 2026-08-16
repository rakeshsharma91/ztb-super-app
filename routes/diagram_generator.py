"""
diagram_generator.py
Deterministic draw.io XML generator for ZTB Current State & Future State
branch architecture diagrams.

Inputs  : keyword_answers dict  (from UserResponse.answers)
Outputs : { 'current_xml': str, 'future_xml': str }
"""

import xml.etree.ElementTree as ET

# ── Zscaler SVG icons (Base64-embedded) ───────────────────────────────────────

ZTB_ICON_B64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyBpZD0i"
    "TGF5ZXJfNCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB2aWV3"
    "Qm94PSIwIDAgMTIwIDEyMCI+CiAgPGRlZnM+CiAgICA8c3R5bGU+CiAgICAgIC5j"
    "bHMtMSB7CiAgICAgICAgZmlsbDogIzIzNmJmNTsKICAgICAgfQogICAgPC9zdHlsZT4K"
    "ICA8L2RlZnM+CiAgPHBhdGggY2xhc3M9ImNscy0xIiBkPSJNOTUuMzIsNDcuODFI"
    "MjQuNjhjLTIuOTMsMC01LjMyLDIuMzktNS4zMiw1LjMydjEzLjc0YzAsMi45Mywy"
    "LjM5LDUuMzIsNS4zMiw1LjMyaDcwLjY0YzIuOTMsMCw1LjMyLTIuMzksNS4zMi01"
    "LjMydi0xMy43NGMwLTIuOTMtMi4zOS01LjMyLTUuMzItNS4zMlpNOTUuMzIsNjgu"
    "ODRIMjQuNjhjLTEuMDksMC0xLjk3LS44OC0xLjk3LTEuOTd2LTEzLjc0YzAtMS4w"
    "OS44OC0xLjk3LDEuOTctMS45N2g3MC42NGMxLjA5LDAsMS45Ny44OCwxLjk3LDEu"
    "OTd2MTMuNzRoMGMwLDEuMDktLjg4LDEuOTctMS45NywxLjk3Wk00Mi4zNSw2MC4z"
    "NmMtLjUxLTMuMTgtNS45NC0yLjU1LTcuNS0uMjIuNDItLjI2LDQuMDgtMS44MSw1"
    "Ljc0LjA3LjQ2LjUzLDAsMS45Mi0xLjg1LDEuMzMtMy40My0xLjExLTYuMjQsMS4w"
    "My03LjE2LDIuMjMuNDUuNTIsMS4wNS43OCwyLjE0LjYyLDIuNTMsMS4yNSw1LjQ2"
    "LjA5LDYuMjgtMS42MSwxLjMxLS4xLDIuNTktLjk0LDIuMzUtMi40MlpNMzguMzMs"
    "NTYuNDhjLS43Ny0uODktNC40Ni0xLjUzLTYuNTYuNTktMi42MS0uNTItNC40Mywx"
    "LjY5LTQuMzMsMy43MS4xMSwyLjAyLDIuMzEsMy4yNywzLjU2LDIuOTMuMDMsMCwu"
    "MDYsMCwuMDksMCwuMjgtMS4zMywxLjQxLTQuNDMsNi4wMi02LjA0LDAsMC0xLjI1"
    "LS40NS0zLjAxLjMxbC0uMjEtLjA5YzEuNjktMS4xMiwzLjE3LTEuNTksNC40NC0x"
    "LjQxWk03OS43NSw1Ni43YzAsLjM1LS4zLjU2LS43LjU2cy0uNy0uMjEtLjctLjU2"
    "YzAtLjMyLjI4LS41NC43LS41NHMuNy4yMi43LjU0Wk03OS43NSw1OC45MmMwLC4z"
    "Mi0uMjguNTQtLjcuNTRzLS43LS4yMi0uNy0uNTRjMC0uMzUuMy0uNTYuNy0uNTZz"
    "LjcuMi43LjU2Wk05MS40Myw1Ny44MWMwLDEuMDItLjY1LDEuNjUtMS41MywxLjY1"
    "cy0xLjUzLS42NC0xLjUzLTEuNjUuNjQtMS42NSwxLjUzLTEuNjUsMS41My42NCwx"
    "LjUzLDEuNjVaTTkzLjM1LDUzLjYxaC00NC4yM2MtLjc2LDAtMS4zNi42MS0xLjM2"
    "LDEuMzZ2MTAuMDZjMCwuNzUuNiwxLjM2LDEuMzYsMS4zNmg0NC4yM2MuNzUsMCwx"
    "LjM2LS42MSwxLjM2LTEuMzZ2LTEwLjA2YzAtLjc1LS42MS0xLjM2LTEuMzYtMS4z"
    "NlpNNTMuMTYsNjMuMzljLS4wMy4wOS0uMDYuMTktLjA5LjI5LS4wNC4xLS4xLjE4"
    "LS4xNS4yNi0uMDYuMS0uMTIuMTctLjIuMjQtLjA3LjA4LS4xNC4xNC0uMjQuMi0u"
    "MDguMDUtLjE2LjExLS4yNy4xNS0uMDkuMDMtLjE5LjA2LS4yOC4wOC0uMS4wMy0u"
    "MjEuMDQtLjMxLjA0cy0uMjEsMC0uMzEtLjA0Yy0uMS0uMDItLjItLjA1LS4yOS0u"
    "MDgtLjA5LS4wNC0uMTktLjEtLjI3LS4xNS0uMDktLjA2LS4xNy0uMTItLjI0LS4y"
    "LS4zLS4yOC0uNDYtLjY5LS40Ni0xLjFzLjE2LS44Mi40Ni0xLjExYy4wNy0uMDcu"
    "MTUtLjE0LjI0LS4xOS4wOC0uMDYuMTgtLjExLjI3LS4xNS4wOS0uMDQuMTktLjA3"
    "LjI5LS4wOC4yLS4wNS40MS0uMDUuNjIsMCwuMDkuMDEuMTkuMDQuMjguMDguMTEu"
    "MDQuMTkuMDkuMjcuMTUuMS4wNS4xNy4xMi4yNC4xOS4wOC4wOC4xNC4xNS4yLjI0"
    "LjA1LjA5LjExLjE3LjE1LjI3LjAzLjA5LjA2LjIuMDkuMjkuMDIuMS4wMy4yMS4w"
    "My4zMXMtLjAxLjIxLS4wMy4zMVpNNTcuNzIsNjQuNjVjLS44NywwLTEuNTctLjcx"
    "LTEuNTctMS41NywwLS40My4xNy0uODIuNDYtMS4xMS4yOS0uMjguNjgtLjQ2LDEu"
    "MTEtLjQ2cy44My4xOCwxLjEuNDZjLjI5LjI5LjQ3LjY4LjQ3LDEuMTEsMCwuODYt"
    "LjcxLDEuNTctMS41NywxLjU3Wk02NC45Myw2NC4xOGMtLjA3LjA4LS4xNS4xNC0u"
    "MjQuMi0uMDkuMDUtLjE3LjExLS4yNy4xNS0uMS4wMy0uMTkuMDYtLjI5LjA4LS4x"
    "LjAzLS4yLjA0LS4zMS4wNC0uMSwwLS4yLDAtLjMtLjA0LS4xLS4wMi0uMjEtLjA1"
    "LS4zLS4wOC0uMDktLjA0LS4xOC0uMS0uMjctLjE1LS4wOC0uMDYtLjE2LS4xMi0u"
    "MjQtLjItLjI4LS4yOC0uNDYtLjY5LS40Ni0xLjEsMC0uMS4wMi0uMjEuMDQtLjMx"
    "LjAyLS4wOS4wNC0uMi4wOS0uMjkuMDQtLjA5LjA4LS4xOC4xNC0uMjcuMDUtLjA5"
    "LjEyLS4xNi4xOS0uMjQuMDgtLjA3LjE2LS4xNC4yNC0uMTkuMDktLjA2LjE4LS4x"
    "MS4yNy0uMTUuMDktLjA0LjItLjA3LjMtLjA4LjItLjA1LjQxLS4wNS42MSwwLC4x"
    "LjAxLjE5LjA0LjI5LjA4LjEuMDQuMTguMDkuMjcuMTUuMDkuMDUuMTcuMTIuMjQu"
    "MTkuMjkuMjkuNDYuNy40NiwxLjExcy0uMTcuODItLjQ2LDEuMVpNNzEuNTcsNTUu"
    "ODVsLTIuODUsMy42MWgyLjg1djEuMWgtNC41di0uOGwyLjg1LTMuNjFoLTIuODV2"
    "LTEuMWg0LjV2LjhaTTc2Ljk4LDU2LjE2aC0xLjk5djQuNDFoLTEuMXYtNC40MWgt"
    "MS45OXYtMS4xaDUuMDl2MS4xWk04MC44Niw1OS4wNWMwLC45MS0uNzMsMS41MS0x"
    "LjgsMS41MXMtMS44LS42LTEuOC0xLjUxYzAtLjU3LjI1LS45OS43My0xLjI0LS40"
    "NS0uMjQtLjczLS42OS0uNzMtMS4yNCwwLS45MS43My0xLjUxLDEuOC0xLjUxczEu"
    "OC42LDEuOCwxLjVjMCwuNTQtLjI4LDEtLjc0LDEuMjUuNDkuMjYuNzQuNjguNzQs"
    "MS4yNFpNODQuMzQsNjAuNTdjLTEuNDcsMC0yLjYzLTEuMTEtMi42My0yLjc2czEu"
    "MTYtMi43NiwyLjYzLTIuNzYsMi42MywxLjExLDIuNjMsMi43Ni0xLjE2LDIuNzYt"
    "Mi42MywyLjc2Wk04OS45LDYwLjU3Yy0xLjQ3LDAtMi42My0xLjExLTIuNjMtMi43"
    "NnMxLjE2LTIuNzYsMi42My0yLjc2LDIuNjMsMS4xMSwyLjYzLDIuNzYtMS4xNiwy"
    "Ljc2LTIuNjMsMi43NlpNODUuODcsNTcuODFjMCwxLjAyLS42NSwxLjY1LTEuNTMs"
    "MS42NXMtMS41My0uNjQtMS41My0xLjY1LjY0LTEuNjUsMS41My0xLjY1LDEuNTMu"
    "NjQsMS41MywxLjY1WiIvPgo8L3N2Zz4="
)

ZTE_ICON_B64 = (
    "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPHN2ZyBpZD0i"
    "TGF5ZXJfMSIgZGF0YS1uYW1lPSJMYXllciAxIiB4bWxucz0iaHR0cDovL3d3dy53"
    "My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAxMDUuNzIgNjYuMjQiPgogIDxk"
    "ZWZzPgogICAgPHN0eWxlPgogICAgICAuY2xzLTEgewogICAgICAgIGZpbGw6ICMyNTZj"
    "Zjc7CiAgICAgIH0KCiAgICAgIC5jbHMtMSwgLmNscy0yLCAuY2xzLTMgewogICAgICAg"
    "IGZpbGwtcnVsZTogZXZlbm9kZDsKICAgICAgICBzdHJva2Utd2lkdGg6IDBweDsKICAg"
    "ICAgfQoKICAgICAgLmNscy0yIHsKICAgICAgICBmaWxsOiAjZmZmOwogICAgICB9CgogI"
    "CAgICAuY2xzLTMgewogICAgICAgIGZpbGw6ICNhN2M1ZmY7CiAgICAgICAgb3BhY2l0eT"
    "ogLjM7CiAgICAgIH0KICAgIDwvc3R5bGU+CiAgPC9kZWZzPgogIDxwYXRoIGNsYXNzPSJj"
    "bHMtMSIgZD0iTTEwNS41MiwzMy44Yy0xLjU3LTkuODEtOS41Ni0xNC41Ny0xOS4wMy0x"
    "NS41LS4yNC0uMDItLjQ5LS4wNS0uNzQtLjA3aC4wNHMtMi41Mi02Ljk1LTguNjktMTIu"
    "MjhoLS4wMXMtLjA2LS4wNi0uMDktLjA5Yy0xLjExLS45Ni0yLjIzLTEuNzctMy4zOS0y"
    "LjQ1LTIuODEtMS40NS02LjczLTIuNTktMTEuMi0zLjExLTIuNzEtLjMyLTUuNjItLjQt"
    "OC41OS0uMTctOC4wOC41OS0xNi42NiwzLjQ0LTIzLjE0LDkuOTktNi45LTEuMzctMTMu"
    "MDItLjAyLTE3Ljk1LDIuOTUtLjA2LjA0LS4xMy4wOC0uMTkuMTItLjMuMTgtLjYuMzgt"
    "Ljg4LjU3LS4xNC4wOS0uMjcuMTktLjQyLjI5LS4yMy4xNi0uNDcuMzQtLjcuNTEtLjEz"
    "LjA5LS4yNS4xOS0uMzkuMy0uMjkuMjQtLjU4LjQ3LS44Ni43Mi0uMDQuMDMtLjA3LjA2"
    "LS4xMS4wOUMzLjA5LDIwLjk4LS4zNywyOS4wMS4wMywzNi42NmMuNzQsMTQuNDIsMTYu"
    "MzIsMjMuNCwyNS4yLDIwLjk3LjIxLS4wNi40NCwwLC42NCwwLC43MS40MywzLjQyLjQy"
    "LDMuNDIuNDIsMy4yNSwzLjcsNy40Nyw1LjY0LDE1LjE0LDQuNDYsMTUuMTIsNy40OCwz"
    "Mi4yLDIuODEsNDAuNzMtNi4xMy4xMi0uMTMuMjQtLjI3LjM2LS40LjA5LS4xLjE4LS4x"
    "OS4yNi0uMywxLjExLTEuMzEsMi4wNy0yLjcxLDIuOS00LjE1LjEtLjE4LjItLjM4LjI5"
    "LS41Niw2LjA0LS40NSwxMi4wNC0zLjE3LDE0Ljk3LTcuOTcsMS40OC0yLjUxLDIuMTQt"
    "NS41OSwxLjU2LTkuMTloLjAxWiIvPgogIDxwYXRoIGNsYXNzPSJjbHMtMyIgZD0iTTkz"
    "LjEsMzIuNjZjLTEyLjIzLTE0LjAzLTM5Ljg2LTEuMzktNDAuODUtLjM1LDYuMDgtOS4z"
    "OSwyMC45Ni0xNC45OSwzMy41LTE0LjA3aC4wNHMtMi41Mi02Ljk1LTguNjktMTIuMjho"
    "LS4wMWMtOC45Ni0xLjMzLTE5LjQzLDIuMDctMzEuMzksMTAuMDgsMCwwLDEuNC42OCwx"
    "LjQ3LjY0LDEyLjQyLTUuNDIsMjEuMzEtMi4yNSwyMS4yNC0yLjIzQzM1Ljg4LDI1Ljkz"
    "LDI3Ljg2LDQ4LjExLDI1Ljg4LDU3LjYzYy43MS40MywzLjQyLjQyLDMuNDIuNDIsNi41"
    "Ni04LjUzLDI2LjQ1LTIzLjg4LDUwLjczLTE1Ljk2LDEyLjk2LDQuMjMsMTYuMzMtNS43"
    "MSwxMy4wNy05LjQ0aC0uMDFaIi8+CiAgPHBhdGggY2xhc3M9ImNscy0yIiBkPSJNMTku"
    "OTYsMjEuODdoNy40NnYxLjMybC00LjczLDUuOThoNC43M3YxLjgzaC03LjQ2di0xLjMx"
    "bDQuNzMtNmgtNC43M3YtMS44M1pNNTIuMzgsMjEuODdoOC40NHYxLjgzaC0zLjMxdjcu"
    "MzFoLTEuODN2LTcuMzFoLTMuM3YtMS44M1pNODIuMzksMjIuNzRoMS43MnYxLjc1aDEu"
    "NjV2MS40NWgtMS42NXYyLjgzYzAsLjQxLjIxLjU5LjY1LjU5LjI2LDAsLjQ4LS4wMi45"
    "Ni0uMTF2MS42M2gwYy0uNDguMTMtLjk4LjIxLTEuNDIuMjEtMS4yMiwwLTEuOTItLjU4"
    "LTEuOTItMi4wN3YtMy4wOGgtMS4xOXYtMS40NWgxLjE5di0xLjc1Wk0zMS45MSwyNC4z"
    "M2MxLjk5LDAsMy4yMiwxLjM3LDMuMjIsMy40N3YuNDdoLTQuOHYuMDJjLjIyLjg3LDEs"
    "MS4yNSwxLjc2LDEuMjVzMS4zOS0uMjcsMS44NS0uNjZsLjcyLDEuNDNjLS41My40NS0x"
    "LjM1Ljg2LTIuNi44Ni0yLjIxLDAtMy40OS0xLjQ4LTMuNDktMy40MnMxLjMtMy40Miwz"
    "LjM0LTMuNDJaTTQwLjA5LDI0LjMzYy4yNCwwLC40NC4wNC42NC4wOXYxLjg1Yy0uMjQt"
    "LjA4LS41MS0uMTEtLjc4LS4xMS0xLjEzLDAtMS42NC42NC0xLjY0LDEuODl2Mi45NWgt"
    "MS43MnYtNi41M2gxLjY1djEuMDljLjM1LS43Ni45NC0xLjIzLDEuODUtMS4yM1pNNDUu"
    "MDUsMjQuMzNjMi4wMSwwLDMuNTIsMS4zOCwzLjUyLDMuNDJzLTEuNSwzLjQyLTMuNTIs"
    "My40Mi0zLjUyLTEuMzgtMy41Mi0zLjQyLDEuNS0zLjQyLDMuNTItMy40MlpNNjUuNDgs"
    "MjQuMzNjLjI0LDAsLjQ0LjA0LjY0LjA5djEuODVjLS4yNC0uMDgtLjUxLS4xMS0uNzgt"
    "LjExLTEuMTMsMC0xLjY0LjY0LTEuNjQsMS44OXYyLjk1aC0xLjcydi02LjUzaDEuNjV2"
    "MS4wOWMuMzUtLjc2Ljk0LTEuMjMsMS44NS0xLjIzWk03Ny44MywyNC4zM2gwYzEuMTcu"
    "MDEsMi4wMS4zNiwyLjYuOThsLS45NywxLjI1Yy0uMzktLjQ0LTEuMTEtLjY2LTEuNzct"
    "LjY2LS41MywwLS44My4xNy0uODMuNDYsMCwuMzIuMzIuMzgsMS41MS42NSwxLjI0LjI4"
    "LDIuMDkuNzQsMi4wOSwyLjA1LDAsMS40NC0xLjAyLDIuMTMtMi44MiwyLjEzLTEuMzEs"
    "MC0yLjM0LS4zOS0yLjktMS4wOWwxLTEuMzFjLjQxLjQ4LDEuMS44NSwyLjA4Ljg1LjQ4"
    "LDAsLjg2LS4xMy44Ni0uNSwwLS4zNC0uMzMtLjQxLTEuNDUtLjY2LTEuMDItLjIyLTIu"
    "MTctLjY2LTIuMTctMi4wN3MxLjA1LTIuMDgsMi43NS0yLjA4Wk03MS42LDI0LjQ5aDEu"
    "NzV2Ni41M2gtMS42OHYtLjk5Yy0uNDUuNjYtMS4xLDEuMTUtMi4wOCwxLjE1LTEuNTEs"
    "MC0yLjI2LTEuMDItMi4yNi0yLjYydi00LjA2aDEuNzZ2My42MmMwLC45Mi4zNCwxLjM5"
    "LDEuMSwxLjM5Ljk3LDAsMS40LS43OCwxLjQtMS45di0zLjEyWk0zMS44NywyNS43OWMt"
    "LjgzLDAtMS4zNy40NC0xLjU1LDEuMjNoMi45NGMtLjA4LS43MS0uNTctMS4yMy0xLjM5"
    "LTEuMjNaTTQ1LjA1LDI2LjAyYy0uOTgsMC0xLjc0LjctMS43NCwxLjc0cy43NiwxLjcz"
    "LDEuNzQsMS43MywxLjczLS43LDEuNzMtMS43My0uNzYtMS43NC0xLjczLTEuNzRaTTIz"
    "LjEyLDMzLjg1aDUuOXYxLjgzaC00LjA3djEuODNoNC4wN3YxLjgzaC00LjA3djEuODNo"
    "NC4wN3YxLjgzaC01Ljl2LTkuMTRaTTQ1LjM5LDMzLjg3aDEuNzJ2My41OGMuNDgtLjc3"
    "LDEuMTktMS4xMywyLjA3LTEuMTMsMS40OSwwLDIuMzEuOTQsMi4zMSwyLjYzdjQuMDVo"
    "LTEuNzZ2LTMuNjFjMC0uOTItLjQxLTEuNC0xLjE5LTEuNC0uOTQsMC0xLjQzLjY1LTEu"
    "NDMsMS45djMuMTJoLTEuNzJ2LTkuMTRaTTcxLjI5LDM2LjN2LjAyYy45MSwwLDEuNzIu"
    "NCwyLjEzLDEuMDd2LS45MWgxLjcydjYuMDljMCwyLjA5LTEuMjQsMy4yMS0zLjU1LDMu"
    "MjEtMS4yMiwwLTIuMTQtLjMzLTIuODktMS4wMmwuODUtMS40M2MuNTcuNTQsMS4yLjgy"
    "LDEuOTguODIsMS4yNiwwLDEuOTEtLjU3LDEuOTEtMS42OXYtLjQxYy0uNDUuNjQtMS4y"
    "LDEtMi4xLDEtMS44NSwwLTMuMDctMS4zMy0zLjA3LTMuMzVzMS4yNC0zLjQsMy4wMi0z"
    "LjRaTTQxLjU4LDM2LjMxYy45OSwwLDEuODUuMzMsMi40OC45NmwtLjk4LDEuMzhjLS40"
    "NC0uNDQtLjkzLS42NS0xLjUtLjY1LTEsMC0xLjcxLjcyLTEuNzEsMS43NHMuNzEsMS43"
    "MywxLjcxLDEuNzNjLjU4LDAsMS4xLS4yNCwxLjU1LS42NmwuOTYsMS4zOGMtLjYzLjYz"
    "LTEuNTEuOTctMi41My45Ny0yLjA1LDAtMy40Ni0xLjM5LTMuNDYtMy40MnMxLjQ0LTMu"
    "NDIsMy40OC0zLjQyaDBaTTU2LjA5LDM2LjMxYzEuNjgsMCwyLjgyLjc0LDIuODIsMi40"
    "M2guMDF2NC4yOGgtMS43MnYtLjg5Yy0uNDEuNjQtMS4xLDEuMDMtMiwxLjAzLTEuMzEs"
    "MC0yLjIyLS44NC0yLjIyLTJzLjgyLTEuODQsMi4xOS0xLjk5bDEuMjMtLjEzYy42MS0u"
    "MDcuNzktLjI1Ljc5LS41NywwLS4zNy0uMzktLjYtMS4wNy0uNi0uOSwwLTEuNDkuMzIt"
    "MS43Ljg1bC0xLjI4LS45MWMuNC0uOTYsMS40NC0xLjQ5LDIuOTUtMS40OVpNNjQuNTMs"
    "MzYuMzFjMS40NiwwLDIuMy45NCwyLjMsMi42djQuMDhoLTEuNzZ2LTMuNjFjMC0uOTIt"
    "LjQxLTEuNC0xLjIyLTEuNC0uOTEsMC0xLjM5LjY2LTEuMzksMS45djMuMTJoLTEuNzN2"
    "LTYuNTNoMS42OHYuOTljLjUtLjc2LDEuMjUtMS4xNSwyLjEzLTEuMTVaTTc5Ljk3LDM2"
    "LjMyYzEuOTksMCwzLjIyLDEuMzcsMy4yMiwzLjQ3di40N2gtNC44di4wMmMuMjIuODcs"
    "MSwxLjI1LDEuNzYsMS4yNXMxLjM5LS4yNywxLjg1LS42NmwuNzIsMS40M2MtLjUzLjQ1"
    "LTEuMzUuODYtMi42Ljg2LTIuMjEsMC0zLjUtMS40OC0zLjUtMy40MnMxLjMtMy40Miwy"
    "LjM0LTMuNDJaTTMwLjI2LDM2LjQ2aDIuMDhsMS4zOSwxLjgzLDEuMzktMS44M2gyLjA5"
    "bC0yLjQ0LDMuMTksMi41NSwzLjM0aC0yLjA4bC0xLjUxLTEuOTctMS41LDEuOTdoLTIu"
    "MDhsMi41NS0zLjM0LTIuNDQtMy4xOVpNNzkuOTMsMzcuNzhjLS44MywwLTEuMzcuNDQt"
    "MS41NSwxLjIzaDIuOTRjLS4wOC0uNzEtLjU3LTEuMjMtMS4zOS0xLjIzWk03MS43OCwz"
    "OGMtMS4wMiwwLTEuNzIuNzItMS43MiwxLjc1cy43MSwxLjc1LDEuNzIsMS43NSwxLjY5"
    "LS43MSwxLjY5LTEuNzUtLjY3LTEuNzUtMS42OS0xLjc1Wk01Ny4yMSwzOS45OGMtLjIx"
    "LjEzLS40Ni4yMS0uNzQuMjVsLS44My4xMWMtLjU3LjA3LS44Ni4zNC0uODYuNzMsMCwu"
    "NDYuMzUuNzQuOTQuNzQuODcsMCwxLjQ5LS42MywxLjQ5LTEuNDl2LS4zNFoiLz4KPC9z"
    "dmc+"
)

# ── Style constants ────────────────────────────────────────────────────────────

S_INTERNET   = "ellipse;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;"
S_MPLS       = "ellipse;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;"
S_SDWAN      = "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;"
S_NGFW       = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ffe6cc;strokeColor=#d79b00;"
S_NAC        = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450;"
S_L3         = "rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
S_L2         = "rounded=0;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;"
S_ZTB        = f"shape=image;verticalLabelPosition=bottom;verticalAlign=top;html=1;image=data:image/svg+xml;base64,{ZTB_ICON_B64};"
S_ZTE        = f"shape=image;verticalLabelPosition=bottom;verticalAlign=top;html=1;image=data:image/svg+xml;base64,{ZTE_ICON_B64};"
S_MICROSEG   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#0070c0;strokeColor=#005a9e;fontColor=#ffffff;"
S_CONTAINER  = "swimlane;startSize=20;fillColor=#f5f5f5;strokeColor=#666666;fontColor=#333333;fontSize=10;"
S_DEVNODE    = "rounded=1;whiteSpace=wrap;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontSize=10;"
S_EDGE       = "edgeStyle=orthogonalEdgeStyle;html=1;"
S_EDGE_DASH  = "edgeStyle=orthogonalEdgeStyle;html=1;dashed=1;endArrow=none;strokeColor=#FF0000;"

# ── Layout constants ───────────────────────────────────────────────────────────

W_CLOUD  = 120; H_CLOUD  = 60
W_APP    = 140; H_APP    = 60
W_SW     = 140; H_SW     = 60
W_ZTB    = 160; H_ZTB    = 60
W_ZTE    = 180; H_ZTE    = 80
W_MICROSEG = 180; H_MICROSEG = 60
W_CONT   = 160; H_CONT   = 80
W_DEV    = 120; H_DEV    = 40

Y_WAN    = 40
Y_SEC    = 160
Y_SW     = 300
Y_MICROSEG_ROW = 420
Y_DEV_WITH_MICROSEG = 540
Y_DEV_NO_MICROSEG   = 420

ZTE_X = 580
ZTE_Y = 40

# ── Keyword normalisation helpers ──────────────────────────────────────────────

def _norm(val):
    """Lowercase, strip a string or first item of list."""
    if isinstance(val, list):
        return [str(v).strip().lower() for v in val]
    return str(val or '').strip().lower()

def _contains_any(haystack_str, needles):
    h = haystack_str.lower()
    return any(n.lower() in h for n in needles)

def _list_contains_any(lst, needles):
    return any(_contains_any(item, needles) for item in (lst or []))

# ── XML builder helpers ────────────────────────────────────────────────────────

def _make_model():
    root = ET.Element('mxGraphModel')
    r = ET.SubElement(root, 'root')
    ET.SubElement(r, 'mxCell', id='0')
    ET.SubElement(r, 'mxCell', id='1', parent='0')
    return root, r

def _vert(parent_el, cid, label, style, x, y, w, h):
    cell = ET.SubElement(parent_el, 'mxCell',
        id=str(cid), value=label, style=style,
        vertex='1', parent='1')
    ET.SubElement(cell, 'mxGeometry',
        x=str(x), y=str(y), width=str(w), height=str(h),
        **{'as': 'geometry'})
    return cell

def _container(parent_el, cid, label, x, y, w, h):
    cell = ET.SubElement(parent_el, 'mxCell',
        id=str(cid), value=label, style=S_CONTAINER,
        vertex='1', parent='1')
    ET.SubElement(cell, 'mxGeometry',
        x=str(x), y=str(y), width=str(w), height=str(h),
        **{'as': 'geometry'})
    return cell

def _dev_node(parent_el, cid, label, cont_id, x, y, w, h):
    cell = ET.SubElement(parent_el, 'mxCell',
        id=str(cid), value=label, style=S_DEVNODE,
        vertex='1', parent=str(cont_id))
    ET.SubElement(cell, 'mxGeometry',
        x=str(x), y=str(y), width=str(w), height=str(h),
        **{'as': 'geometry'})
    return cell

def _edge(parent_el, cid, src, tgt, style=None):
    s = style if style else S_EDGE
    cell = ET.SubElement(parent_el, 'mxCell',
        id=str(cid), value='', style=s,
        edge='1', source=str(src), target=str(tgt), parent='1')
    ET.SubElement(cell, 'mxGeometry', relative='1', **{'as': 'geometry'})
    return cell

def _to_xml_str(root_el):
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root_el, encoding='unicode')

# ── Parse assessment answers ───────────────────────────────────────────────────

def _parse_answers(answers):
    """
    Extract the fields the diagram needs from the keyword_answers dict.
    Returns a normalised dict of parsed values.
    """
    def get(key):
        return answers.get(key, '') or ''

    vertical       = _norm(get('gen_vertical'))
    scope_raw      = _norm(get('vp_scope'))
    wan_raw        = _norm(get('vp_wan_link_types'))
    solutions_raw  = get('vp_current_vendor')  # list or string
    sdwan_vendor   = _norm(get('vp_sdwan_vendor'))
    fw_vendor      = _norm(get('vp_firewall_vendor'))
    devices_raw    = get('dp_site_devices')    # list or string

    # Scope
    has_sdwan_scope = _contains_any(str(scope_raw), ['sd-wan', 'sdwan'])
    has_seg_scope   = _contains_any(str(scope_raw), ['segmentation', 'seg'])

    # WAN
    has_mpls = _contains_any(str(wan_raw), ['mpls', 'private'])

    # Current solutions
    if isinstance(solutions_raw, list):
        sol_str = ' '.join(solutions_raw).lower()
    else:
        sol_str = str(solutions_raw or '').lower()
    has_sdwan_sol = 'sdwan' in sol_str or 'sd-wan' in sol_str or 'sd wan' in sol_str
    has_ngfw_sol  = 'ngfw' in sol_str or 'firewall' in sol_str or 'ngfw' in sol_str
    has_nac_sol   = 'nac' in sol_str

    # SD-WAN vendor validity
    sdwan_vendor_valid = (
        has_sdwan_sol and
        sdwan_vendor and
        'not in list' not in sdwan_vendor and
        'no sd-wan' not in sdwan_vendor and
        'no sdwan' not in sdwan_vendor and
        sdwan_vendor.strip() != ''
    )

    # NGFW vendor validity
    fw_vendor_valid = (
        has_ngfw_sol and
        fw_vendor and
        'n/a' not in fw_vendor and
        'no firewall' not in fw_vendor and
        fw_vendor.strip() != ''
    )

    # Devices — normalise to list of display labels
    if isinstance(devices_raw, list):
        raw_devices = [str(d).strip() for d in devices_raw if d]
    elif devices_raw:
        raw_devices = [d.strip() for d in str(devices_raw).split(',') if d.strip()]
    else:
        raw_devices = []

    if not raw_devices:
        raw_devices = ['Users with ZCC', 'IoT Devices', 'Printers']

    # Cap at 4 general device containers
    device_containers = raw_devices[:4]

    # Vertical additions (always appended, not counted toward the cap)
    vertical_str = str(vertical)
    if 'healthcare' in vertical_str:
        device_containers.append('Medical Devices')
    elif 'federal' in vertical_str:
        device_containers.append('Classified Endpoints')
    elif 'sled' in vertical_str:
        device_containers.append('Student Devices')
        device_containers.append('Administrative Systems')

    # SD-WAN vendor label
    sdwan_label = ''
    if sdwan_vendor_valid:
        # Title-case the vendor name
        sdwan_label = ' '.join(w.capitalize() for w in sdwan_vendor.split()) + '&#xa;SD-WAN'

    fw_label = ''
    if fw_vendor_valid:
        fw_label = ' '.join(w.capitalize() for w in fw_vendor.split()) + '&#xa;NGFW'

    return {
        'has_sdwan_scope':    has_sdwan_scope,
        'has_seg_scope':      has_seg_scope,
        'has_mpls':           has_mpls,
        'sdwan_vendor_valid': sdwan_vendor_valid,
        'fw_vendor_valid':    fw_vendor_valid,
        'has_nac_sol':        has_nac_sol,
        'sdwan_label':        sdwan_label,
        'fw_label':           fw_label,
        'device_containers':  device_containers,
    }

# ── Current State builder ──────────────────────────────────────────────────────

def _build_current(p, answers):
    root, r = _make_model()
    cid = 2  # ID counter

    has_mpls           = p['has_mpls']
    sdwan_vendor_valid = p['sdwan_vendor_valid']
    fw_vendor_valid    = p['fw_vendor_valid']
    has_nac_sol        = p['has_nac_sol']
    device_containers  = p['device_containers']

    # ── WAN layer ──
    internet_id = cid
    _vert(r, cid, 'Internet', S_INTERNET, 160, Y_WAN, W_CLOUD, H_CLOUD); cid += 1

    mpls_id = None
    if has_mpls:
        mpls_id = cid
        _vert(r, cid, 'MPLS / Private Circuit', S_MPLS, 400, Y_WAN, W_CLOUD, H_CLOUD); cid += 1

    # ── Security layer (top-to-bottom order): SD-WAN → NGFW ──
    sec_ids = []  # list of (id) in chain order

    if sdwan_vendor_valid:
        sid = cid
        _vert(r, cid, p['sdwan_label'], S_SDWAN, 280, Y_SEC, W_APP, H_APP); cid += 1
        sec_ids.append(sid)

    if fw_vendor_valid:
        fid = cid
        # place to the right of SD-WAN if present
        fx = 280 + (W_APP + 20) * len(sec_ids)
        _vert(r, cid, p['fw_label'], S_NGFW, fx, Y_SEC, W_APP, H_APP); cid += 1
        sec_ids.append(fid)

    # ── L3 Switch ──
    l3_id = cid
    _vert(r, cid, 'Layer 3 Core Switch', S_L3, 280, Y_SW, W_SW, H_SW); cid += 1

    # ── NAC (after L3 switch) ──
    nac_id = None
    if has_nac_sol:
        nac_id = cid
        _vert(r, cid, 'NAC', S_NAC, 460, Y_SW, W_APP, H_APP); cid += 1

    # ── Device containers ──
    y_dev = Y_DEV_NO_MICROSEG
    n_dev = len(device_containers)
    total_w = n_dev * W_CONT + (n_dev - 1) * 20
    x_start = max(40, 320 - total_w // 2)

    container_ids = []
    for i, dev_label in enumerate(device_containers):
        cx = x_start + i * (W_CONT + 20)
        cont_id = cid
        _container(r, cid, dev_label, cx, y_dev, W_CONT, H_CONT); cid += 1
        _dev_node(r, cid, dev_label.split()[0], cont_id, 20, 25, W_DEV, H_DEV); cid += 1
        container_ids.append(cont_id)

    # ── Edges ──
    first_sec = sec_ids[0] if sec_ids else l3_id

    # WAN → first security box (or L3 if no security boxes)
    _edge(r, cid, internet_id, first_sec); cid += 1
    if mpls_id:
        _edge(r, cid, mpls_id, first_sec); cid += 1

    # Chain security boxes
    for i in range(len(sec_ids) - 1):
        _edge(r, cid, sec_ids[i], sec_ids[i+1]); cid += 1

    # Last sec box → L3
    if sec_ids:
        _edge(r, cid, sec_ids[-1], l3_id); cid += 1

    # L3 → NAC (if present), then NAC / L3 → devices
    if nac_id:
        _edge(r, cid, l3_id, nac_id); cid += 1
        last_before_devs = nac_id
    else:
        last_before_devs = l3_id

    for cont_id in container_ids:
        _edge(r, cid, last_before_devs, cont_id); cid += 1

    return _to_xml_str(root)

# ── Future State builder ───────────────────────────────────────────────────────

def _build_future(p, answers):
    root, r = _make_model()
    cid = 2

    has_seg_scope     = p['has_seg_scope']
    device_containers = p['device_containers']

    # ── WAN: Internet only (no MPLS in future state) ──
    internet_id = cid
    _vert(r, cid, 'Internet', S_INTERNET, 160, Y_WAN, W_CLOUD, H_CLOUD); cid += 1

    # ── ZTE (top right, fixed position) ──
    zte_id = cid
    _vert(r, cid, 'Zero Trust Exchange&#xa;ZIA · ZPA · ZDX', S_ZTE, ZTE_X, ZTE_Y, W_ZTE, H_ZTE); cid += 1

    # ── ZTB Appliance ──
    ztb_id = cid
    _vert(r, cid, 'ZTB Appliance', S_ZTB, 280, Y_SEC, W_ZTB, H_ZTB); cid += 1

    # ── L2 Switch ──
    l2_id = cid
    _vert(r, cid, 'Layer 2 Switch', S_L2, 280, Y_SW, W_SW, H_SW); cid += 1

    # ── Microsegmentation engine (only if Segmentation in scope) ──
    microseg_id = None
    if has_seg_scope:
        microseg_id = cid
        _vert(r, cid, 'ZTB Microsegmentation&#xa;L2 Policy Engine', S_MICROSEG,
              240, Y_MICROSEG_ROW, W_MICROSEG, H_MICROSEG); cid += 1

    # ── Device containers ──
    y_dev = Y_DEV_WITH_MICROSEG if has_seg_scope else Y_DEV_NO_MICROSEG
    n_dev = len(device_containers)
    total_w = n_dev * W_CONT + (n_dev - 1) * 20
    x_start = max(40, 320 - total_w // 2)

    container_ids = []
    for i, dev_label in enumerate(device_containers):
        cx = x_start + i * (W_CONT + 20)
        cont_id = cid
        _container(r, cid, dev_label, cx, y_dev, W_CONT, H_CONT); cid += 1
        _dev_node(r, cid, dev_label.split()[0], cont_id, 20, 25, W_DEV, H_DEV); cid += 1
        container_ids.append(cont_id)

    # ── Edges ──
    _edge(r, cid, internet_id, ztb_id); cid += 1
    _edge(r, cid, ztb_id, zte_id); cid += 1
    _edge(r, cid, ztb_id, l2_id); cid += 1

    if microseg_id:
        _edge(r, cid, l2_id, microseg_id); cid += 1
        for cont_id in container_ids:
            _edge(r, cid, microseg_id, cont_id, style=S_EDGE_DASH); cid += 1
    else:
        for cont_id in container_ids:
            _edge(r, cid, l2_id, cont_id); cid += 1

    return _to_xml_str(root)

# ── Public entry point ─────────────────────────────────────────────────────────

def generate_diagram_xml(answers: dict) -> dict:
    """
    Given a keyword_answers dict (from UserResponse.answers),
    return { 'current_xml': str, 'future_xml': str }.
    """
    p = _parse_answers(answers)
    return {
        'current_xml': _build_current(p, answers),
        'future_xml':  _build_future(p, answers),
    }
