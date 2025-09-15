--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (84ade85)
-- Dumped by pg_dump version 16.9

-- Started on 2025-09-15 02:51:02 UTC

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE ONLY public.user_interactions DROP CONSTRAINT user_interactions_user_id_fkey;
ALTER TABLE ONLY public.user_interactions DROP CONSTRAINT user_interactions_scholarship_id_fkey;
DROP INDEX public.ix_user_profiles_state_of_residence;
DROP INDEX public.ix_user_profiles_grade_level;
DROP INDEX public.ix_user_profiles_gpa;
DROP INDEX public.ix_user_profiles_financial_need;
DROP INDEX public.ix_user_profiles_field_of_study;
DROP INDEX public.ix_user_profiles_citizenship;
DROP INDEX public.ix_user_profiles_age;
DROP INDEX public.ix_user_interactions_user_id;
DROP INDEX public.ix_user_interactions_timestamp;
DROP INDEX public.ix_user_interactions_source;
DROP INDEX public.ix_user_interactions_session_id;
DROP INDEX public.ix_user_interactions_scholarship_id;
DROP INDEX public.ix_user_interactions_interaction_type;
DROP INDEX public.ix_search_analytics_user_id;
DROP INDEX public.ix_search_analytics_timestamp;
DROP INDEX public.ix_search_analytics_session_id;
DROP INDEX public.ix_search_analytics_search_query;
DROP INDEX public.ix_scholarships_scholarship_type;
DROP INDEX public.ix_scholarships_organization;
DROP INDEX public.ix_scholarships_name;
DROP INDEX public.ix_scholarships_is_active;
DROP INDEX public.ix_scholarships_application_deadline;
DROP INDEX public.ix_scholarships_amount;
DROP INDEX public.ix_organizations_name;
DROP INDEX public.ix_interactions_user_id;
DROP INDEX public.ix_interactions_user_created;
DROP INDEX public.ix_interactions_trace_id;
DROP INDEX public.ix_interactions_scholarship_id;
DROP INDEX public.ix_interactions_scholarship_created;
DROP INDEX public.ix_interactions_event_type;
DROP INDEX public.ix_interactions_event_created;
DROP INDEX public.ix_interactions_created_at;
DROP INDEX public.idx_scholarships_type_btree;
DROP INDEX public.idx_scholarships_name_btree;
DROP INDEX public.idx_scholarships_deadline_btree;
DROP INDEX public.idx_scholarships_amount_btree;
ALTER TABLE ONLY public.user_profiles DROP CONSTRAINT user_profiles_pkey;
ALTER TABLE ONLY public.user_interactions DROP CONSTRAINT user_interactions_pkey;
ALTER TABLE ONLY public.search_analytics DROP CONSTRAINT search_analytics_pkey;
ALTER TABLE ONLY public.scholarships DROP CONSTRAINT scholarships_pkey;
ALTER TABLE ONLY public.organizations DROP CONSTRAINT organizations_pkey;
ALTER TABLE ONLY public.interactions DROP CONSTRAINT interactions_pkey;
DROP TABLE public.user_profiles;
DROP TABLE public.user_interactions;
DROP TABLE public.search_analytics;
DROP TABLE public.scholarships;
DROP TABLE public.organizations;
DROP TABLE public.interactions;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 220 (class 1259 OID 32768)
-- Name: interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.interactions (
    id character varying NOT NULL,
    event_type character varying(100) NOT NULL,
    user_id character varying(100),
    scholarship_id character varying(100),
    path character varying(500) NOT NULL,
    method character varying(10) NOT NULL,
    status integer NOT NULL,
    trace_id character varying(100),
    request_metadata json,
    created_at timestamp with time zone NOT NULL
);


--
-- TOC entry 217 (class 1259 OID 24603)
-- Name: organizations; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.organizations (
    id character varying NOT NULL,
    name character varying(255) NOT NULL,
    description text,
    website character varying(500),
    contact_email character varying(255),
    contact_phone character varying(50),
    organization_type character varying(100),
    established_year integer,
    total_awards_given integer,
    total_amount_awarded double precision,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_active boolean
);


--
-- TOC entry 215 (class 1259 OID 24576)
-- Name: scholarships; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.scholarships (
    id character varying NOT NULL,
    name character varying(255) NOT NULL,
    organization character varying(255) NOT NULL,
    description text NOT NULL,
    amount double precision NOT NULL,
    max_awards integer,
    application_deadline timestamp without time zone NOT NULL,
    notification_date timestamp without time zone,
    scholarship_type character varying(50) NOT NULL,
    application_url character varying(500),
    contact_email character varying(255),
    renewable boolean,
    eligibility_criteria json NOT NULL,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_active boolean
);


--
-- TOC entry 218 (class 1259 OID 24611)
-- Name: search_analytics; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.search_analytics (
    id character varying NOT NULL,
    search_query character varying(500),
    filters_applied json,
    results_count integer NOT NULL,
    user_id character varying,
    response_time_ms double precision,
    clicked_results character varying[],
    search_quality_score double precision,
    "timestamp" timestamp without time zone,
    session_id character varying(100),
    user_agent character varying(500),
    ip_address character varying(45)
);


--
-- TOC entry 219 (class 1259 OID 24622)
-- Name: user_interactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_interactions (
    id character varying NOT NULL,
    user_id character varying NOT NULL,
    scholarship_id character varying NOT NULL,
    interaction_type character varying(50) NOT NULL,
    search_query character varying(500),
    filters_applied json,
    match_score double precision,
    position_in_results integer,
    "timestamp" timestamp without time zone,
    session_id character varying(100),
    source character varying(50)
);


--
-- TOC entry 216 (class 1259 OID 24589)
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_profiles (
    id character varying NOT NULL,
    gpa double precision,
    grade_level character varying(50),
    field_of_study character varying(100),
    citizenship character varying(50),
    state_of_residence character varying(2),
    age integer,
    financial_need boolean,
    extracurricular_activities character varying[],
    work_experience json,
    academic_achievements json,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    is_active boolean
);


--
-- TOC entry 3397 (class 0 OID 32768)
-- Dependencies: 220
-- Data for Name: interactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.interactions (id, event_type, user_id, scholarship_id, path, method, status, trace_id, request_metadata, created_at) FROM stdin;
4442f03a-88b9-4ba7-8e3d-662019bcfe6e	view	user-456	test-123	/interactions/log	POST	200	54339d87-359a-49c0-8292-63cddb6243e7	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:42:49.110406+00
61d6817c-93fa-4fa2-8ceb-a2624a2d737c	view	user-456	test-123	/interactions/log	POST	200	21137a49-ecd2-4325-8ef4-b8d11454b93b	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:43:06.917956+00
a635e2cb-fc71-4369-9610-57330f791894	view	user-456	test-123	/interactions/log	POST	200	c94a0322-e29a-4a2e-bf9e-03f581db200f	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:43:20.315132+00
632c2ac9-655b-4575-bd01-7b3d249cef20	view	user-456	test-123	/interactions/log	POST	200	da47fb45-4cff-48c7-b81a-9eed97311434	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:43:44.728187+00
e081cb2a-7ed9-46bf-b93f-b0ae0f253701	view	user-456	test-123	/interactions/log	POST	200	6bc89291-d2d2-4db7-ae69-068542dd021d	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:44:27.904602+00
cd93f87e-b605-4136-a98b-8fe8ca261bfc	view	user-456	test-123	/interactions/log	POST	200	ea3a475c-3817-487e-a3f9-fd3022d28998	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:48:59.930129+00
ff48e91a-3f16-4e91-8351-9f6337c71206	view	user-456	test-123	/interactions/log	POST	200	14fc7302-0c99-4167-972a-8dc102645307	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:52:55.802314+00
443b3984-f2fd-409a-9c07-4eb7d6919745	view	user-456	test-123	/interactions/log	POST	200	45ad9616-74bc-4ebb-8f1b-17f8223b40ef	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 16:54:24.096858+00
18317d49-7eb6-41c8-88ea-6fdac86d6d5a	view	user-456	test-123	/interactions/log	POST	200	4fec3f45-1b32-4cf6-a673-225e7f32a506	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 17:01:10.214769+00
bf40f7f9-42b7-4d06-8cc4-f1a08915a800	view	user-456	test-123	/interactions/log	POST	200	c8436b8b-4ccc-48d6-8d72-084b96b5480f	{"search_query": null, "filters": null, "custom_metadata": null, "user_agent": "testclient"}	2025-08-18 17:25:41.477023+00
\.


--
-- TOC entry 3394 (class 0 OID 24603)
-- Dependencies: 217
-- Data for Name: organizations; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.organizations (id, name, description, website, contact_email, contact_phone, organization_type, established_year, total_awards_given, total_amount_awarded, created_at, updated_at, is_active) FROM stdin;
\.


--
-- TOC entry 3392 (class 0 OID 24576)
-- Dependencies: 215
-- Data for Name: scholarships; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.scholarships (id, name, organization, description, amount, max_awards, application_deadline, notification_date, scholarship_type, application_url, contact_email, renewable, eligibility_criteria, created_at, updated_at, is_active) FROM stdin;
sch_001	National Merit Engineering Scholarship	Engineering Excellence Foundation	A prestigious scholarship for outstanding engineering students who demonstrate academic excellence, leadership qualities, and commitment to innovation. This scholarship supports students pursuing degrees in various engineering disciplines including mechanical, electrical, civil, and computer engineering.	15000	50	2025-12-15 00:00:00	2026-02-01 00:00:00	merit_based	https://example.com/apply/engineering-scholarship	scholarships@engineering-excellence.org	t	{"min_gpa": 3.5, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": ["engineering", "technology"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371216	2025-08-17 23:05:14.371219	t
sch_002	Future Healthcare Leaders Award	Medical Professionals Association	Supporting the next generation of healthcare professionals through financial assistance and mentorship opportunities. Open to students pursuing careers in medicine, nursing, pharmacy, physical therapy, and other healthcare fields.	8000	25	2025-11-30 00:00:00	2026-01-15 00:00:00	academic_achievement	https://example.com/apply/healthcare-scholarship	awards@medical-professionals.org	f	{"min_gpa": 3.2, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": "US", "residency_states": ["CA", "NY", "TX", "FL", "IL"], "fields_of_study": ["medicine", "science"], "min_age": 18, "max_age": 30, "financial_need": null, "essay_required": true, "recommendation_letters": 3}	2025-08-17 23:05:14.37122	2025-08-17 23:05:14.37122	t
sch_003	Business Innovation Grant	Entrepreneurship Institute	Encouraging entrepreneurial spirit and business innovation among students. This scholarship is designed for students who have demonstrated leadership in business ventures, startup experience, or innovative business ideas.	12000	30	2025-10-31 00:00:00	2025-12-15 00:00:00	merit_based	https://example.com/apply/business-innovation	grants@entrepreneurship-institute.org	t	{"min_gpa": 3.0, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": null, "residency_states": [], "fields_of_study": ["business"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 1}	2025-08-17 23:05:14.371222	2025-08-17 23:05:14.371222	t
sch_004	Need-Based Student Support Fund	Community Education Foundation	Providing financial assistance to students from low-income families who demonstrate financial need and academic potential. This scholarship aims to remove financial barriers to higher education.	5000	100	2026-03-01 00:00:00	2026-04-15 00:00:00	need_based	https://example.com/apply/need-based-support	support@community-education.org	t	{"min_gpa": 2.5, "max_gpa": null, "grade_levels": ["undergraduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": true, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371223	2025-08-17 23:05:14.371223	t
sch_005	Arts and Creativity Scholarship	Creative Arts Society	Supporting talented students in visual arts, performing arts, creative writing, and digital media. Recipients must demonstrate exceptional artistic ability and commitment to their craft.	7500	20	2026-01-15 00:00:00	2026-03-01 00:00:00	merit_based	https://example.com/apply/arts-creativity	scholarships@creative-arts-society.org	f	{"min_gpa": 2.8, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": null, "residency_states": [], "fields_of_study": ["arts"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371224	2025-08-17 23:05:14.371224	t
sch_006	STEM Excellence Award	Science & Technology Foundation	Recognizing outstanding achievements in Science, Technology, Engineering, and Mathematics. This award supports students who have demonstrated excellence in STEM fields and plan to pursue careers in scientific research or technology development.	20000	15	2025-12-31 00:00:00	2026-02-15 00:00:00	academic_achievement	https://example.com/apply/stem-excellence	awards@stem-foundation.org	t	{"min_gpa": 3.7, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": ["science", "technology", "engineering"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 3}	2025-08-17 23:05:14.371225	2025-08-17 23:05:14.371225	t
sch_007	Community Service Leadership Award	Civic Engagement Alliance	Honoring students who have made significant contributions to their communities through volunteer work and civic engagement. This scholarship recognizes leadership in community service and social impact initiatives.	6000	40	2026-02-28 00:00:00	2026-04-01 00:00:00	community_service	https://example.com/apply/community-service	awards@civic-engagement.org	f	{"min_gpa": 3.0, "max_gpa": null, "grade_levels": ["undergraduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371225	2025-08-17 23:05:14.371226	t
sch_008	First-Generation College Student Grant	Educational Access Foundation	Supporting first-generation college students who are the first in their families to pursue higher education. This grant provides financial assistance and mentorship to help students succeed in their academic journey.	4500	75	2026-04-30 00:00:00	2026-06-15 00:00:00	need_based	https://example.com/apply/first-generation	grants@educational-access.org	t	{"min_gpa": 2.5, "max_gpa": null, "grade_levels": ["undergraduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": true, "essay_required": true, "recommendation_letters": 1}	2025-08-17 23:05:14.371226	2025-08-17 23:05:14.371226	t
sch_009	International Student Excellence Award	Global Education Initiative	Supporting outstanding international students pursuing higher education in the United States. This award recognizes academic excellence and cross-cultural leadership among international students.	10000	25	2025-11-15 00:00:00	2026-01-01 00:00:00	merit_based	https://example.com/apply/international-excellence	international@global-education.org	f	{"min_gpa": 3.4, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": null, "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371227	2025-08-17 23:05:14.371227	t
sch_010	Women in Technology Scholarship	Tech Diversity Coalition	Encouraging women to pursue careers in technology and computer science. This scholarship supports female students in STEM fields with a focus on technology, programming, and digital innovation.	9000	35	2025-12-01 00:00:00	2026-01-30 00:00:00	minority	https://example.com/apply/women-in-tech	scholarships@tech-diversity.org	t	{"min_gpa": 3.2, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": ["technology", "engineering", "science"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371227	2025-08-17 23:05:14.371228	t
sch_011	Rural Community Education Fund	Rural Development Alliance	Supporting students from rural communities who face unique challenges in accessing higher education. This fund provides financial assistance to help rural students pursue their educational goals.	3500	60	2026-03-15 00:00:00	2026-05-01 00:00:00	need_based	https://example.com/apply/rural-education	rural-fund@development-alliance.org	t	{"min_gpa": 2.7, "max_gpa": null, "grade_levels": ["undergraduate"], "citizenship_required": "US", "residency_states": ["MT", "WY", "ND", "SD", "NE", "KS", "OK", "TX", "NM"], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": true, "essay_required": true, "recommendation_letters": 1}	2025-08-17 23:05:14.371233	2025-08-17 23:05:14.371233	t
sch_012	Graduate Research Excellence Award	Academic Research Council	Supporting exceptional graduate students conducting groundbreaking research across various disciplines. This award recognizes students whose research has the potential for significant academic and societal impact.	18000	12	2025-10-15 00:00:00	2025-12-01 00:00:00	academic_achievement	https://example.com/apply/graduate-research	research-awards@academic-council.org	f	{"min_gpa": 3.8, "max_gpa": null, "grade_levels": ["graduate"], "citizenship_required": null, "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 3}	2025-08-17 23:05:14.371233	2025-08-17 23:05:14.371233	t
sch_013	Legal Studies Scholarship	Justice Education Foundation	Supporting students pursuing legal education and careers in law. This scholarship is available to pre-law undergraduates and law school students who demonstrate academic excellence and commitment to justice.	11000	20	2026-01-31 00:00:00	2026-03-15 00:00:00	merit_based	https://example.com/apply/legal-studies	legal-scholarships@justice-education.org	f	{"min_gpa": 3.4, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": ["law"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371234	2025-08-17 23:05:14.371234	t
sch_014	Social Sciences Research Grant	Behavioral Research Institute	Funding research projects in psychology, sociology, anthropology, and related social science fields. This grant supports students conducting innovative research that contributes to our understanding of human behavior and society.	6500	30	2026-02-15 00:00:00	2026-04-01 00:00:00	academic_achievement	https://example.com/apply/social-sciences	grants@behavioral-research.org	f	{"min_gpa": 3.3, "max_gpa": null, "grade_levels": ["undergraduate", "graduate"], "citizenship_required": null, "residency_states": [], "fields_of_study": ["social_sciences"], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371234	2025-08-17 23:05:14.371235	t
sch_015	Athletic Academic Achievement Award	Student Athlete Foundation	Recognizing student-athletes who excel both in their sport and in the classroom. This award supports student-athletes who demonstrate outstanding academic performance while participating in competitive sports.	7000	45	2025-11-30 00:00:00	2026-01-15 00:00:00	athletic	https://example.com/apply/athletic-academic	athletics@student-athlete-foundation.org	t	{"min_gpa": 3.0, "max_gpa": null, "grade_levels": ["undergraduate"], "citizenship_required": "US", "residency_states": [], "fields_of_study": [], "min_age": null, "max_age": null, "financial_need": null, "essay_required": true, "recommendation_letters": 2}	2025-08-17 23:05:14.371235	2025-08-17 23:05:14.371235	t
\.


--
-- TOC entry 3395 (class 0 OID 24611)
-- Dependencies: 218
-- Data for Name: search_analytics; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.search_analytics (id, search_query, filters_applied, results_count, user_id, response_time_ms, clicked_results, search_quality_score, "timestamp", session_id, user_agent, ip_address) FROM stdin;
\.


--
-- TOC entry 3396 (class 0 OID 24622)
-- Dependencies: 219
-- Data for Name: user_interactions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_interactions (id, user_id, scholarship_id, interaction_type, search_query, filters_applied, match_score, position_in_results, "timestamp", session_id, source) FROM stdin;
757f97c4-211f-4f94-98ea-16188ff766a8	admin	sch_001	viewed	engineering	{"min_gpa": 3.0}	0.85	1	2025-08-17 23:43:44.050323	\N	search
9f53b2d2-8e96-4763-a7b5-39cb039013ae	admin	sch_001	viewed	engineering	{"min_gpa": 3.0}	0.85	1	2025-08-17 23:44:10.584952	\N	search
fe81be2f-8110-4b04-906c-1ad377eb486d	admin	sch_001	viewed	engineering	{"min_gpa": 3.0}	0.85	1	2025-08-17 23:45:39.687132	\N	search
a29ced95-4954-4a92-82fe-c64d9f8c64af	admin	sch_001	viewed	engineering	{"min_gpa": 3.0}	0.85	1	2025-08-17 23:46:17.138118	\N	search
cd826326-4a5b-4088-b05d-0a2c93c491ee	admin	sch_001	viewed	engineering	{"min_gpa": 3.0}	0.85	1	2025-08-17 23:46:22.611023	\N	search
\.


--
-- TOC entry 3393 (class 0 OID 24589)
-- Dependencies: 216
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_profiles (id, gpa, grade_level, field_of_study, citizenship, state_of_residence, age, financial_need, extracurricular_activities, work_experience, academic_achievements, created_at, updated_at, is_active) FROM stdin;
admin	4	graduate	computer_science	US	CA	25	f	\N	\N	\N	\N	\N	\N
test_user_1	3.5	undergraduate	engineering	US	NY	20	t	\N	\N	\N	\N	\N	\N
test_user_2	3.8	graduate	medicine	US	TX	24	f	\N	\N	\N	\N	\N	\N
test_user_3	3.2	undergraduate	business	US	FL	21	t	\N	\N	\N	\N	\N	\N
\.


--
-- TOC entry 3238 (class 2606 OID 32774)
-- Name: interactions interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.interactions
    ADD CONSTRAINT interactions_pkey PRIMARY KEY (id);


--
-- TOC entry 3222 (class 2606 OID 24609)
-- Name: organizations organizations_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.organizations
    ADD CONSTRAINT organizations_pkey PRIMARY KEY (id);


--
-- TOC entry 3210 (class 2606 OID 24582)
-- Name: scholarships scholarships_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.scholarships
    ADD CONSTRAINT scholarships_pkey PRIMARY KEY (id);


--
-- TOC entry 3228 (class 2606 OID 24617)
-- Name: search_analytics search_analytics_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.search_analytics
    ADD CONSTRAINT search_analytics_pkey PRIMARY KEY (id);


--
-- TOC entry 3236 (class 2606 OID 24628)
-- Name: user_interactions user_interactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_pkey PRIMARY KEY (id);


--
-- TOC entry 3219 (class 2606 OID 24595)
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (id);


--
-- TOC entry 3199 (class 1259 OID 40963)
-- Name: idx_scholarships_amount_btree; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarships_amount_btree ON public.scholarships USING btree (amount);


--
-- TOC entry 3200 (class 1259 OID 40961)
-- Name: idx_scholarships_deadline_btree; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarships_deadline_btree ON public.scholarships USING btree (application_deadline);


--
-- TOC entry 3201 (class 1259 OID 40960)
-- Name: idx_scholarships_name_btree; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarships_name_btree ON public.scholarships USING btree (name);


--
-- TOC entry 3202 (class 1259 OID 40962)
-- Name: idx_scholarships_type_btree; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_scholarships_type_btree ON public.scholarships USING btree (scholarship_type);


--
-- TOC entry 3239 (class 1259 OID 32779)
-- Name: ix_interactions_created_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_created_at ON public.interactions USING btree (created_at);


--
-- TOC entry 3240 (class 1259 OID 32782)
-- Name: ix_interactions_event_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_event_created ON public.interactions USING btree (event_type, created_at);


--
-- TOC entry 3241 (class 1259 OID 32777)
-- Name: ix_interactions_event_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_event_type ON public.interactions USING btree (event_type);


--
-- TOC entry 3242 (class 1259 OID 32780)
-- Name: ix_interactions_scholarship_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_scholarship_created ON public.interactions USING btree (scholarship_id, created_at);


--
-- TOC entry 3243 (class 1259 OID 32775)
-- Name: ix_interactions_scholarship_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_scholarship_id ON public.interactions USING btree (scholarship_id);


--
-- TOC entry 3244 (class 1259 OID 32781)
-- Name: ix_interactions_trace_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_trace_id ON public.interactions USING btree (trace_id);


--
-- TOC entry 3245 (class 1259 OID 32776)
-- Name: ix_interactions_user_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_user_created ON public.interactions USING btree (user_id, created_at);


--
-- TOC entry 3246 (class 1259 OID 32778)
-- Name: ix_interactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_interactions_user_id ON public.interactions USING btree (user_id);


--
-- TOC entry 3220 (class 1259 OID 24610)
-- Name: ix_organizations_name; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX ix_organizations_name ON public.organizations USING btree (name);


--
-- TOC entry 3203 (class 1259 OID 24585)
-- Name: ix_scholarships_amount; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_amount ON public.scholarships USING btree (amount);


--
-- TOC entry 3204 (class 1259 OID 24584)
-- Name: ix_scholarships_application_deadline; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_application_deadline ON public.scholarships USING btree (application_deadline);


--
-- TOC entry 3205 (class 1259 OID 24587)
-- Name: ix_scholarships_is_active; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_is_active ON public.scholarships USING btree (is_active);


--
-- TOC entry 3206 (class 1259 OID 24586)
-- Name: ix_scholarships_name; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_name ON public.scholarships USING btree (name);


--
-- TOC entry 3207 (class 1259 OID 24583)
-- Name: ix_scholarships_organization; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_organization ON public.scholarships USING btree (organization);


--
-- TOC entry 3208 (class 1259 OID 24588)
-- Name: ix_scholarships_scholarship_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_scholarships_scholarship_type ON public.scholarships USING btree (scholarship_type);


--
-- TOC entry 3223 (class 1259 OID 24621)
-- Name: ix_search_analytics_search_query; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_search_analytics_search_query ON public.search_analytics USING btree (search_query);


--
-- TOC entry 3224 (class 1259 OID 24618)
-- Name: ix_search_analytics_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_search_analytics_session_id ON public.search_analytics USING btree (session_id);


--
-- TOC entry 3225 (class 1259 OID 24619)
-- Name: ix_search_analytics_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_search_analytics_timestamp ON public.search_analytics USING btree ("timestamp");


--
-- TOC entry 3226 (class 1259 OID 24620)
-- Name: ix_search_analytics_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_search_analytics_user_id ON public.search_analytics USING btree (user_id);


--
-- TOC entry 3229 (class 1259 OID 24639)
-- Name: ix_user_interactions_interaction_type; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_interaction_type ON public.user_interactions USING btree (interaction_type);


--
-- TOC entry 3230 (class 1259 OID 24642)
-- Name: ix_user_interactions_scholarship_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_scholarship_id ON public.user_interactions USING btree (scholarship_id);


--
-- TOC entry 3231 (class 1259 OID 24644)
-- Name: ix_user_interactions_session_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_session_id ON public.user_interactions USING btree (session_id);


--
-- TOC entry 3232 (class 1259 OID 24641)
-- Name: ix_user_interactions_source; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_source ON public.user_interactions USING btree (source);


--
-- TOC entry 3233 (class 1259 OID 24640)
-- Name: ix_user_interactions_timestamp; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_timestamp ON public.user_interactions USING btree ("timestamp");


--
-- TOC entry 3234 (class 1259 OID 24643)
-- Name: ix_user_interactions_user_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_interactions_user_id ON public.user_interactions USING btree (user_id);


--
-- TOC entry 3211 (class 1259 OID 24601)
-- Name: ix_user_profiles_age; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_age ON public.user_profiles USING btree (age);


--
-- TOC entry 3212 (class 1259 OID 24602)
-- Name: ix_user_profiles_citizenship; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_citizenship ON public.user_profiles USING btree (citizenship);


--
-- TOC entry 3213 (class 1259 OID 24599)
-- Name: ix_user_profiles_field_of_study; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_field_of_study ON public.user_profiles USING btree (field_of_study);


--
-- TOC entry 3214 (class 1259 OID 24600)
-- Name: ix_user_profiles_financial_need; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_financial_need ON public.user_profiles USING btree (financial_need);


--
-- TOC entry 3215 (class 1259 OID 24596)
-- Name: ix_user_profiles_gpa; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_gpa ON public.user_profiles USING btree (gpa);


--
-- TOC entry 3216 (class 1259 OID 24597)
-- Name: ix_user_profiles_grade_level; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_grade_level ON public.user_profiles USING btree (grade_level);


--
-- TOC entry 3217 (class 1259 OID 24598)
-- Name: ix_user_profiles_state_of_residence; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX ix_user_profiles_state_of_residence ON public.user_profiles USING btree (state_of_residence);


--
-- TOC entry 3247 (class 2606 OID 24634)
-- Name: user_interactions user_interactions_scholarship_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_scholarship_id_fkey FOREIGN KEY (scholarship_id) REFERENCES public.scholarships(id);


--
-- TOC entry 3248 (class 2606 OID 24629)
-- Name: user_interactions user_interactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_interactions
    ADD CONSTRAINT user_interactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.user_profiles(id);


-- Completed on 2025-09-15 02:51:05 UTC

--
-- PostgreSQL database dump complete
--

