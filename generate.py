#!/usr/bin/env python3
"""Rebuilds manifest.json from the GitHub releases of the plugins listed in plugins.json.

Each release must carry one plugin zip with a meta.json inside (guid, name, version, targetAbi,
changelog, ...), as the release workflows of the plugin repositories build it. Checksums already in
the manifest are reused, so only new zips are downloaded.

Usage: GITHUB_TOKEN=... ./generate.py   (the token only raises the API rate limit; repos are public)
"""
import hashlib
import io
import json
import os
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def get(url):
    headers = {"User-Agent": "jellyfin-plugins-manifest"}
    if TOKEN and url.startswith("https://api.github.com/"):
        headers["Authorization"] = f"Bearer {TOKEN}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as r:
        return r.read()


def version_key(version):
    return tuple(int(x) for x in version.split("."))


def main():
    old = json.loads((HERE / "manifest.json").read_text())
    known = {v["sourceUrl"]: v for p in old for v in p["versions"]}
    manifest = []

    for entry in json.loads((HERE / "plugins.json").read_text()):
        releases = json.loads(get(f"https://api.github.com/repos/{entry['repo']}/releases?per_page=100"))
        plugin, versions = None, []
        for release in releases:
            if release["draft"] or release["prerelease"] or not release["tag_name"].startswith("v"):
                continue
            zips = [a for a in release["assets"] if a["name"].endswith(".zip")]
            if len(zips) != 1:
                print(f"skip {entry['repo']} {release['tag_name']}: {len(zips)} zip assets")
                continue
            url = zips[0]["browser_download_url"]
            data = None if url in known else get(url)
            if data is not None:
                meta = json.loads(zipfile.ZipFile(io.BytesIO(data)).read("meta.json"))
                version = {
                    "version": meta["version"],
                    "changelog": meta.get("changelog", ""),
                    "targetAbi": meta["targetAbi"],
                    "sourceUrl": url,
                    "checksum": hashlib.md5(data).hexdigest(),
                    "timestamp": meta.get("timestamp", release["published_at"]),
                }
                if plugin is None or version_key(meta["version"]) > version_key(plugin["_version"]):
                    plugin = {k: meta.get(k, "") for k in ("guid", "name", "overview", "description", "owner", "category")}
                    plugin["_version"] = meta["version"]
            else:
                version = known[url]
            versions.append(version)

        if not versions:
            continue
        if plugin is None:  # every version came from the cache: keep the plugin fields
            plugin = next(p for p in old if any(v["sourceUrl"] == versions[0]["sourceUrl"] for v in p["versions"]))
        plugin = {k: v for k, v in plugin.items() if k not in ("_version", "versions", "imageUrl")}
        plugin["imageUrl"] = entry["imageUrl"]
        plugin["versions"] = sorted(versions, key=lambda v: version_key(v["version"]), reverse=True)
        manifest.append(plugin)

    text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
    if text != (HERE / "manifest.json").read_text():
        (HERE / "manifest.json").write_text(text)
        print("manifest.json updated")
    else:
        print("manifest.json unchanged")


if __name__ == "__main__":
    main()
