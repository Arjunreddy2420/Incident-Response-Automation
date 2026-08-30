-- Seed data for local development

INSERT INTO escalation_policies (team_name, severity_level, on_call_engineer, backup_engineer, escalation_time_minutes, slack_channel)
VALUES
    ('payment-platform', 'CRITICAL', 'alice', 'bob', 15, '#payment-platform-incidents'),
    ('payment-platform', 'HIGH', 'alice', 'bob', 30, '#payment-platform-incidents'),
    ('auth', 'CRITICAL', 'carol', 'dave', 15, '#auth-incidents'),
    ('auth', 'HIGH', 'carol', 'dave', 30, '#auth-incidents'),
    ('data-platform', 'CRITICAL', 'erin', 'frank', 15, '#data-platform-incidents'),
    ('data-platform', 'HIGH', 'erin', 'frank', 30, '#data-platform-incidents'),
    ('on-call-general', 'MEDIUM', 'grace', 'heidi', 60, '#general-incidents'),
    ('on-call-general', 'LOW', 'grace', 'heidi', 120, '#general-incidents')
ON CONFLICT (team_name, severity_level) DO NOTHING;

INSERT INTO runbooks (team_name, metric_pattern, title, url, steps)
VALUES
    (
        'payment-platform',
        'payment',
        'Payment Gateway Errors Runbook',
        'https://runbooks.internal/payment-gateway-errors',
        ARRAY[
            'Check the payment gateway provider''s public status page',
            'Verify API credentials for the gateway have not expired',
            'Check recent deploys to payment-service for regressions',
            'Failover to the backup payment processor if errors persist past 10 minutes'
        ]
    ),
    (
        'auth',
        'auth',
        'Auth Login Failures Runbook',
        'https://runbooks.internal/auth-login-failures',
        ARRAY[
            'Check the identity provider''s status page',
            'Verify auth-service pods are healthy and not crash-looping',
            'Check for expired signing certificates or keys',
            'Review recent auth-service deploys for regressions'
        ]
    ),
    (
        'data-platform',
        'db',
        'Database Connection Pool Exhaustion Runbook',
        'https://runbooks.internal/db-connection-pool',
        ARRAY[
            'Compare active connection count against the pool max',
            'Look for long-running or blocked queries',
            'Restart the connection pooler if safe to do so',
            'Scale read replicas if the load is read-driven'
        ]
    ),
    (
        'on-call-general',
        NULL,
        'General Incident Triage Runbook',
        'https://runbooks.internal/general-triage',
        ARRAY[
            'Confirm the alert is not a false positive',
            'Check service health dashboards for the affected system',
            'Identify recent deploys or config changes',
            'Escalate to the owning team if the cause is unclear'
        ]
    )
ON CONFLICT (team_name, metric_pattern) DO NOTHING;
