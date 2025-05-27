-- Initialize BubbleGrade database schema

CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'QUEUED',
    score INTEGER,
    answers JSONB,
    total_questions INTEGER,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_time TIMESTAMP
);

CREATE INDEX idx_scans_status ON scans(status);
CREATE INDEX idx_scans_upload_time ON scans(upload_time);

-- Create sample data
INSERT INTO scans (filename, status, score, answers, total_questions) VALUES 
('sample_test.jpg', 'COMPLETED', 85, '["A", "B", "C", "D", "A"]', 5),
('demo_scan.pdf', 'COMPLETED', 92, '["B", "A", "D", "C", "B"]', 5)
ON CONFLICT DO NOTHING;