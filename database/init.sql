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
