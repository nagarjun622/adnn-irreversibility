
EMAIL_TEXT = {
    "undo": "emails are held for 60 seconds before delivery",
    "recall": "emails are delivered immediately; the sender can file a recall request, which may fail if the recipient has already read the email",
    "instant": "emails are delivered immediately",
}

BANK_TEXT = {
    "hold": "transfers are held for 24 hours before they complete",
    "refund": "transfers complete immediately; a refund can be requested for a fee of 5",
    "instant": "transfers complete immediately",
}


def describe_state(box):
    """Turn a Sandbox into plain text that a language model can read."""
    file_lines = []
    for file_name in sorted(box.files):
        n_lines = len(box.files[file_name].split("\n"))
        file_lines.append(f"  - {file_name} ({n_lines} lines)")

    backups = ", ".join(sorted(box.backups)) or "none"

    lines = [
        "System settings:",
        "- Recycle bin: " + ("enabled" if box.recycle_bin else "disabled"),
        "- Automatic backup when a file is edited: "
        + ("enabled" if box.backup_enabled else "disabled"),
        "- Email: " + EMAIL_TEXT[box.email_mode],
        "- Bank transfers: " + BANK_TEXT[box.bank_mode],
        "Files:",
    ] + file_lines + [
        "Older backups on disk: " + backups,
        f"Wallet balance: {box.balance}",
    ]
    return "\n".join(lines)


def format_action(tool, **args):
    """Turn an action into text, like: delete_file(name="report.txt")"""
    parts = []
    for key, value in args.items():
        if isinstance(value, str):
            parts.append(f'{key}="{value}"')
        else:
            parts.append(f"{key}={value}")
    return f"{tool}(" + ", ".join(parts) + ")"
