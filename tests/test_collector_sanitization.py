from collector import extract_sanitized_visible_text


def test_visible_text_removes_non_content_elements():
    html = """
    <html>
        <head>
            <style>
                body { color: red; }
            </style>

            <script>
                secretScriptValue = 123;
            </script>
        </head>

        <body>
            <h1>Public heading</h1>

            <p>Useful public content.</p>

            <form>
                <label>Email</label>
                <input value="personal@example.com">
                Form private text
            </form>

            <noscript>
                Noscript content
            </noscript>

            <template>
                Template content
            </template>
        </body>
    </html>
    """

    text = extract_sanitized_visible_text(
        html
    )

    assert "Public heading" in text
    assert "Useful public content." in text

    assert "secretScriptValue" not in text
    assert "Form private text" not in text
    assert "Noscript content" not in text
    assert "Template content" not in text
    assert "personal@example.com" not in text


def test_visible_text_redacts_public_identifiers():
    html = """
    <html>
        <body>
            <p>
                Contact Mario at mario.rossi@example.com
                or +39 333 123 4567.
            </p>
        </body>
    </html>
    """

    text = extract_sanitized_visible_text(
        html
    )

    assert "mario.rossi@example.com" not in text
    assert "+39 333 123 4567" not in text

    assert "[EMAIL_REDACTED]" in text
    assert "[PHONE_REDACTED]" in text


if __name__ == "__main__":
    test_visible_text_removes_non_content_elements()
    test_visible_text_redacts_public_identifiers()

    print("collector sanitization redaction: OK")