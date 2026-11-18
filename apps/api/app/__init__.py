"""Cyber Task Hub API paketi."""

import email_validator

# Demo/test hesapları `@demo.local` kullanır (knowledge ACCEPTANCE). email-validator `.local`'i
# özel kullanım alanı sayıp reddeder; yalnızca bu TLD'ye izin veriyoruz.
if "local" in email_validator.SPECIAL_USE_DOMAIN_NAMES:
    email_validator.SPECIAL_USE_DOMAIN_NAMES.remove("local")
