#!/usr/bin/env python3
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "src/main"
CACHE = ROOT / "build-cache"
REF = "39bd3a09640efb81234cdbd8ab98ab71541d5d46"
APKTOOL = "build/apktool/apktool_3.0.2.jar"
TOOLS = {
    APKTOOL: "eee4669a704a14e0623407e6701b0b91887e61e1e4049cb7a82833e14ae8b5fd",
    "build/sign/apksigner.jar": "925fb5189d62fea563eaa24636108cb28a7281c05b63f3478f6c53e7768c7d3b",
    "build/sign/testkey.pk8": "495675d32e89a149d5abe191f4e9c0e218b9068714e9b53a7c91e164a0741a23",
    "build/sign/testkey.x509.pem": "a4384ba815b9499a5ce349b4e33c1755278873fe2eac150a068823f526e6dbde",
}


def tool(source):
    CACHE.mkdir(exist_ok=True)
    destination = CACHE / Path(source).name
    if not destination.exists():
        url = f"https://raw.githubusercontent.com/MindTheGapps/vendor_gapps/{REF}/{source}"
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != TOOLS[source]:
            raise RuntimeError(f"Unexpected tool hash: {destination}")
        destination.write_bytes(data)
    with destination.open("rb") as file:
        if hashlib.file_digest(file, "sha256").hexdigest() != TOOLS[source]:
            raise RuntimeError(f"Unexpected tool hash: {destination}")
    return destination


def run(*args):
    subprocess.run([str(arg) for arg in args], check=True)


def build():
    config = ET.parse(SOURCE / "res/values/config.xml").getroot()
    columns = int(config.find("integer[@name='grid_num_columns']").text)
    rows = int(config.find("integer[@name='grid_num_rows']").text)
    if columns <= 0 or rows <= 0:
        raise ValueError("Grid dimensions must be positive integers")

    # Build a fresh copy so apktool leaves no generated files in the sources.
    project = CACHE / "project"
    if project.exists():
        shutil.rmtree(project)
    shutil.copytree(SOURCE, project)
    unsigned = CACHE / "Launcher3PartnerLayout-unsigned.apk"
    aligned = CACHE / "Launcher3PartnerLayout-aligned.apk"
    output = ROOT / "output/Launcher3PartnerLayout.apk"

    run("java", "-jar", tool(APKTOOL), "b", project, "-p", CACHE / "framework", "-o", unsigned)
    run("zipalign", "-p", "-f", "4", unsigned, aligned)
    run("zipalign", "-c", "-p", "4", aligned)
    return aligned, output


def main():
    parser = argparse.ArgumentParser(description="Build the Launcher3 partner APK.")
    parser.add_argument("--ks", type=Path, help="Path to the signing keystore.")
    parser.add_argument("--ks-key-alias", help="Alias of the key to use for signing.")
    args = parser.parse_args()
    if args.ks_key_alias and not args.ks:
        parser.error("--ks-key-alias requires --ks")
    if args.ks and not args.ks.is_file():
        parser.error(f"Keystore not found: {args.ks}")

    aligned, output = build()
    signer = tool("build/sign/apksigner.jar")
    if args.ks:
        options = ["--ks", args.ks]
        if args.ks_key_alias:
            options += ["--ks-key-alias", args.ks_key_alias]
    else:
        options = ["--key", tool("build/sign/testkey.pk8"),
                   "--cert", tool("build/sign/testkey.x509.pem")]
    signed = CACHE / "Launcher3PartnerLayout-signed.apk"
    run("java", "-jar", signer, "sign", *options,
        "--v4-signing-enabled", "false", "--out", signed, aligned)
    run("java", "-jar", signer, "verify", signed)
    output.parent.mkdir(exist_ok=True)
    shutil.copyfile(signed, output)
    print(f"Built {output}")
    return output


if __name__ == "__main__":
    main()
