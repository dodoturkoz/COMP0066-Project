def display_emergency_numbers() -> None:
    emergency_numbers = {
        "111 can tell you the right place to get help": [
            "Call 111, and select the mental health option",
            "Or go to https://111.nhs.uk/triage/check-your-mental-health-symptoms",
        ],
        "Free listening services": [
            "Call 116123 to talk to Samaritans, or email: jo@samaritans.org for a reply within 24 hours",
            "Text 'SHOUT' to 85258 to contact the Shout Crisis Text Line, or text 'YM' if you're under 19",
            "If you're under 19, you can also call 0800 1111 to talk to Childline. The number will not appear on your phone bill.",
        ],
    }

    print(
        "If you need help for a mental health crisis or emergency, you should "
        + "get immediate expert advice and assessment:"
    )

    for service, contact in emergency_numbers.items():
        print(f"\n{service}:")
        for c in contact:
            print(f" - {c}")

    print(
        "\nThese services offer confidential support from trained volunteers "
        + "and will only share your information if they are "
        + "very worried about you or think you are in immediate danger."
    )
