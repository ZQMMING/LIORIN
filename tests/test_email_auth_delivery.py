"""邮件投递失败撤销挑战；不打印验证码。"""
from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from tongshu.services.email_auth import send_login_code


class EmailDeliveryTests(unittest.TestCase):
    def test_unconfigured_mailer_does_not_issue_code(self):
        store = Mock()
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, 'unavailable'):
                send_login_code(store, 'user@example.com')
        store.issue.assert_not_called()

    def test_delivery_failure_revokes_only_current_challenge(self):
        store = Mock()
        store.can_send.return_value = True
        config = {
            'TONGSHU_SMTP_HOST': 'smtp.example.com',
            'TONGSHU_SMTP_FROM': 'service@example.com',
            'TONGSHU_EMAIL_AUTH_SECRET': 'x' * 32,
        }
        with patch.dict(os.environ, config, clear=True), \
             patch('tongshu.services.email_auth.smtplib.SMTP') as smtp:
            smtp.return_value.__enter__.return_value.send_message.side_effect = RuntimeError('private smtp error')
            with self.assertRaisesRegex(RuntimeError, '^email service unavailable$'):
                send_login_code(store, 'user@example.com')
        store.issue.assert_called_once()
        store.revoke.assert_called_once()
        self.assertEqual(store.issue.call_args.args, store.revoke.call_args.args)
