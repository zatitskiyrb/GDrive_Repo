import re

_SUFFIXES = re.compile(
    r"\b(inc|llc|ltd|limited|corp|corporation|co|gmbh|ag|bv|sas|srl|pty|plc)\.?\b",
    re.IGNORECASE,
)


def normalize_company(name: str) -> str:
    name = name.strip().lower()
    name = _SUFFIXES.sub("", name)
    name = re.sub(r"[^\w\s]", "", name)
    return re.sub(r"\s+", " ", name).strip()
