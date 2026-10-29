#!/usr/bin/env python3
"""Build the code-native pixel typography and UI, not the generated illustration."""
from pathlib import Path

try:
    from .pixel_art import pixel_text, pixel_width, svg
except ImportError:
    from pixel_art import pixel_text, pixel_width, svg

ASSETS = Path(__file__).resolve().parents[1] / "assets"
INK, CREAM, AMBER, TEAL = "#101a20", "#f2d5a0", "#dea85e", "#86b5a6"


def save(name, width, height, title, body):
    (ASSETS / name).write_text(svg(width, height, title, body), encoding="utf-8")


def main():
    name = "DANIEL MÉNDEZ"
    body = f'<path d="M8 0H952V8H960V112H0V8H8Z" fill="{INK}"/>'
    body += pixel_text((960 - pixel_width(name, 7)) / 2, 24, name, 7)
    body += pixel_text((960 - pixel_width("WEB / BACKEND / MOBILE", 2)) / 2, 89,
                       "WEB / BACKEND / MOBILE", 2, TEAL)
    for x in (28, 922):
        body += f'<path d="M{x} 38h10v10h10v10h-10v10h-10v-10h-10v-10h10Z" fill="{AMBER}"/>'
    save("pixel-name.svg", 960, 112, "Daniel Méndez — web, backend and mobile developer", body)

    # Actual pixel paths rather than a rounded UI with a monospace font.
    for slug, label, width in [("email", "SAY HELLO", 160), ("linkedin", "LINKEDIN", 150),
                               ("projects", "REPOSITORIES", 200)]:
        fill = AMBER if slug == "email" else INK
        color = INK if slug == "email" else CREAM
        body = f'<path d="M4 0H{width-8}V4H{width-4}V36H{width-8}V40H4V36H0V4H4Z" fill="#725f47"/>'
        body += f'<path d="M6 2H{width-10}V6H{width-6}V32H{width-10}V36H6V32H2V6H6Z" fill="{fill}"/>'
        body += pixel_text((width - pixel_width(label)) / 2 - 2, 12, label, 2, color)
        save(f"pixel-{slug}.svg", width, 42, label, body)

    for slug, label in [("about", "ABOUT ME"), ("stack", "TOOLS OF THE TRADE"),
                        ("projects", "SIDE PROJECTS"), ("stats", "GITHUB / SAVE FILE")]:
        width = pixel_width(label) + 58
        body = f'<path d="M4 0H{width}V32H0V4H4Z" fill="{INK}"/>'
        body += pixel_text(10, 9, ">", 2, AMBER)
        body += pixel_text(34, 9, label, 2, CREAM)
        save(f"heading-{slug}.svg", width, 32, label.title(), body)

    body = f'<rect width="960" height="32" fill="{INK}"/>'
    body += '<path d="M0 0H960" stroke="#725f47" stroke-width="2"/>'
    body += pixel_text((960 - pixel_width("THANKS FOR STOPPING BY", 2)) / 2, 10,
                       "THANKS FOR STOPPING BY", 2, TEAL)
    save("pixel-footer.svg", 960, 32, "Thanks for stopping by", body)

    # Eight small, original pixel symbols. No downloaded icon/font service.
    sprites = {
        "TS": ('<rect width="16" height="16" fill="#83a5bf"/>', 'TS', INK),
        "JS": ('<rect width="16" height="16" fill="#dea85e"/>', 'JS', INK),
        "REACT": ('<path d="M6 1h4v2h2v2h3v2h1v2h-1v2h-3v2h-2v2H6v-2H4v-2H1V9H0V7h1V5h3V3h2Z M6 3v2H4v2H2v2h2v2h2v2h4v-2h2V9h2V7h-2V5h-2V3Z" fill="#86b5a6" fill-rule="evenodd"/><rect x="6" y="6" width="4" height="4" fill="#86b5a6"/>', '', ''),
        "NODE": ('<path d="M6 0h4v2h4v2h2v8h-2v2h-4v2H6v-2H2v-2H0V4h2V2h4Z" fill="#91a57b"/>', 'N', INK),
        "KOTLIN": ('<path d="M0 0h16v2h-2v2h-2v2h-2v4h2v2h2v2h2v2H0Z" fill="#bd8979"/><path d="M0 0h10v2H8v2H6v2H4v2H2v2H0Z" fill="#dea85e"/>', '', ''),
        "DOCKER": ('<path d="M1 8h12V6h2V4h1v5h-1v3h-2v2H4v-1H2v-2H1Z" fill="#83a5bf"/><path d="M2 4h3v3H2zM6 4h3v3H6zM10 4h3v3h-3zM6 0h3v3H6z" fill="#83a5bf"/>', '', ''),
        "SQL": ('<path d="M3 0h10v1h2v14h-2v1H3v-1H1V1h2Z" fill="#c3bd89"/><path d="M1 4h14v2H1zM1 10h14v2H1z" fill="#667365"/>', '', ''),
        "GIT": ('<path d="M6 0h4v2h2v2h2v2h2v4h-2v2h-2v2h-2v2H6v-2H4v-2H2v-2H0V6h2V4h2V2h2Z" fill="#c88866"/><path d="M4 4h3v3H4zM9 7h3v3H9zM6 11h3v3H6zM5 6h2v6h1V6H7V5H5Z" fill="#101a20"/>', '', ''),
    }
    atom = ["0001100000011000", "0010010000100100", "0010010000100100",
            "0001001001001000", "0001111111111000", "0110010000100110",
            "1000001111000001", "1000001111000001", "0110010000100110",
            "0001111111111000", "0001001001001000", "0010010000100100",
            "0010010000100100", "0001100000011000"]
    atom_path = "".join(f"M{x} {y+1}h1v1h-1z" for y, row in enumerate(atom)
                        for x, bit in enumerate(row) if bit == "1")
    sprites["REACT"] = (f'<path d="{atom_path}" fill="{TEAL}"/>', '', '')
    for slug, names in [("web", ["TS", "JS", "REACT", "NODE"]),
                        ("systems", ["KOTLIN", "DOCKER", "SQL", "GIT"])]:
        body = f'<path d="M4 0H436V4H440V112H0V4H4Z" fill="{INK}"/>'
        body += '<path d="M12 106H428" stroke="#475552" stroke-width="2"/>'
        for i, label in enumerate(names):
            x = 55 + i * 110
            sprite, letters, color = sprites[label]
            body += f'<g transform="translate({x-24} 15) scale(3)" shape-rendering="crispEdges">{sprite}</g>'
            if letters:
                body += pixel_text(x - pixel_width(letters, 2) / 2, 29, letters, 2, color)
            body += pixel_text(x - pixel_width(label, 1.5) / 2, 80, label, 1.5, CREAM)
        save(f"pixel-stack-{slug}.svg", 440, 120, ", ".join(names), body)


if __name__ == "__main__":
    main()
