-- ==============================================================================
-- FinEasy AI: Supabase PostgreSQL Database Schema
-- Educational Prototype: Individual ITR Workflow (V1)
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ------------------------------------------------------------------------------
-- 1. PROFILES TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    user_type VARCHAR(20) NOT NULL DEFAULT 'individual' CHECK (user_type IN ('individual', 'ca', 'admin')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 2. FILINGS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS filings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    financial_year VARCHAR(10) NOT NULL,
    filing_type VARCHAR(20) NOT NULL DEFAULT 'ITR',
    status VARCHAR(30) NOT NULL DEFAULT 'draft' CHECK (
        status IN (
            'draft',
            'document_uploaded',
            'analysing',
            'analysed',
            'calculation_complete',
            'validation_pending',
            'ca_review',
            'approved',
            'changes_requested',
            'submitted',
            'rejected'
        )
    ),
    gross_income NUMERIC(14, 2) DEFAULT 0.00,
    deductions NUMERIC(14, 2) DEFAULT 0.00,
    taxable_income NUMERIC(14, 2) DEFAULT 0.00,
    tax_amount NUMERIC(14, 2) DEFAULT 0.00,
    tds_amount NUMERIC(14, 2) DEFAULT 0.00,
    refund_amount NUMERIC(14, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 3. DOCUMENTS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    filing_id UUID NOT NULL REFERENCES filings(id) ON DELETE CASCADE,
    file_name VARCHAR(255) NOT NULL,
    document_type VARCHAR(30) NOT NULL DEFAULT 'form_16' CHECK (
        document_type IN ('form_16', 'salary_slip', 'bank_statement', 'other')
    ),
    storage_path TEXT NOT NULL,
    extracted_text TEXT,
    upload_status VARCHAR(30) DEFAULT 'uploaded' CHECK (
        upload_status IN ('uploaded', 'processing', 'extracted', 'failed')
    ),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 4. AI_ANALYSIS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ai_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filings(id) ON DELETE CASCADE,
    employer_name VARCHAR(255),
    gross_salary NUMERIC(14, 2),
    tds NUMERIC(14, 2),
    financial_year VARCHAR(10),
    extracted_data JSONB DEFAULT '{}'::jsonb,
    confidence_score NUMERIC(4, 2) DEFAULT 0.0,
    warnings JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 5. TAX_CALCULATIONS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS tax_calculations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filings(id) ON DELETE CASCADE,
    gross_income NUMERIC(14, 2) NOT NULL,
    deductions NUMERIC(14, 2) NOT NULL,
    taxable_income NUMERIC(14, 2) NOT NULL,
    tax_amount NUMERIC(14, 2) NOT NULL,
    cess NUMERIC(14, 2) NOT NULL,
    total_tax NUMERIC(14, 2) NOT NULL,
    tds NUMERIC(14, 2) NOT NULL,
    refund_or_payable NUMERIC(14, 2) NOT NULL,
    calculation_version VARCHAR(50) DEFAULT 'demo-v1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- 6. REVIEWS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filing_id UUID NOT NULL REFERENCES filings(id) ON DELETE CASCADE,
    reviewer_id UUID,
    status VARCHAR(30) NOT NULL DEFAULT 'pending' CHECK (
        status IN ('pending', 'approved', 'rejected', 'changes_requested')
    ),
    comments TEXT,
    reviewed_at TIMESTAMPTZ
);

-- ------------------------------------------------------------------------------
-- 7. AUDIT_LOGS TABLE
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID,
    filing_id UUID,
    action VARCHAR(50) NOT NULL,
    details JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ------------------------------------------------------------------------------
-- INDEXES FOR PERFORMANCE
-- ------------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_filings_user_id ON filings(user_id);
CREATE INDEX IF NOT EXISTS idx_filings_status ON filings(status);
CREATE INDEX IF NOT EXISTS idx_documents_filing_id ON documents(filing_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_filing_id ON ai_analysis(filing_id);
CREATE INDEX IF NOT EXISTS idx_tax_calculations_filing_id ON tax_calculations(filing_id);
CREATE INDEX IF NOT EXISTS idx_reviews_filing_id ON reviews(filing_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_filing_id ON audit_logs(filing_id);

-- ------------------------------------------------------------------------------
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ------------------------------------------------------------------------------
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE filings ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_calculations ENABLE ROW LEVEL SECURITY;
ALTER TABLE reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can view & update their own profile; admins view all
CREATE POLICY profiles_select_own ON profiles
    FOR SELECT USING (auth.uid() = user_id OR EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('admin', 'ca')
    ));

CREATE POLICY profiles_update_own ON profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Filings: Individuals can access their own; CA can view reviewable filings; Admins full access
CREATE POLICY filings_individual_all ON filings
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY filings_ca_select ON filings
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
    ));

-- Documents: Users access documents of their filings
CREATE POLICY documents_owner_all ON documents
    FOR ALL USING (auth.uid() = user_id);

CREATE POLICY documents_ca_select ON documents
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
    ));

-- AI Analysis & Tax Calculations: Accessible by filing owners and CAs
CREATE POLICY ai_analysis_access ON ai_analysis
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM filings WHERE filings.id = ai_analysis.filing_id AND (
            filings.user_id = auth.uid() OR EXISTS (
                SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
            )
        )
    ));

CREATE POLICY tax_calc_access ON tax_calculations
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM filings WHERE filings.id = tax_calculations.filing_id AND (
            filings.user_id = auth.uid() OR EXISTS (
                SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
            )
        )
    ));

-- Reviews: Viewable by filing owner and CA; only CA/Admin can insert/update
CREATE POLICY reviews_select ON reviews
    FOR SELECT USING (EXISTS (
        SELECT 1 FROM filings WHERE filings.id = reviews.filing_id AND filings.user_id = auth.uid()
    ) OR EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
    ));

CREATE POLICY reviews_ca_write ON reviews
    FOR ALL USING (EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type IN ('ca', 'admin')
    ));

-- Audit Logs: Backend service role has full access; users can view logs for their filings
CREATE POLICY audit_logs_select ON audit_logs
    FOR SELECT USING (auth.uid() = user_id OR EXISTS (
        SELECT 1 FROM profiles WHERE profiles.user_id = auth.uid() AND profiles.user_type = 'admin'
    ));
