--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Ubuntu 17.5-0ubuntu0.25.04.1)
-- Dumped by pg_dump version 17.5 (Ubuntu 17.5-0ubuntu0.25.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
4	Moderador de usuarios
5	Encargado de clientes
\.

--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
26	4	17
27	2	24
28	2	25
29	5	18
30	5	20
\.


--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (id, nombre, apellido, "tipoDocCliente", "docCliente", "correoElecCliente", telefono, "tipoCliente", direccion, ocupacion, declaracion_jurada, created_at, updated_at) FROM stdin;
1	Juan	Pérez	CI	1231231	juanperez@example.com	0981123123	F	Asunción, Paraguay	Estudiante	t	2025-09-03 12:36:01.401701-03	2025-09-03 12:38:32.291502-03
\.

--
-- Data for Name: monedas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monedas (id, nombre, simbolo, activa, tasa_base, decimales) FROM stdin;
2	Euro	EUR	t	8000	3
3	Peso argentino	ARG	t	10	5
1	Dólar estadounidense	USD	t	7400	3
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (group_ptr_id, descripcion) FROM stdin;
4	Rol encargado de verificar que los usuarios sean bienvenidos o no al sistema
5	Rol encargado de la gestión y asignación de clientes.
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (id, password, last_login, is_superuser, username, first_name, last_name, email, tipo_cedula, cedula_identidad, bloqueado, is_active, date_joined, cliente_activo_id) FROM stdin;
3	pbkdf2_sha256$1000000$KUtO3Kz9sYyDujs6givUsm$VVkcJj72tGebc5JKVfCC9OcdmKFwxr20mwyo0fYqECU=	2025-09-03 12:33:58.499498-03	f	irismendoza	Iris	Mendoza	iris@example.com	CI	7897897	f	t	2025-09-03 12:26:33.888296-03	\N
4	pbkdf2_sha256$1000000$nZ5bZGdPP4MeFsTQG0VxIc$NswnhxthPgnIjpC2ub27BMXWi9bdOmR8m/CDLbOwsLM=	2025-09-03 12:37:04.904755-03	f	aylen	Aylen	Wyder	aylen@example.com	CI	4564564	f	t	2025-09-03 12:31:58.921293-03	\N
2	pbkdf2_sha256$1000000$gG25IPHhpfNHXpI6vKQYCg$1lsAHqYbrXyYWF+DKB6IgNE0sweuyzyfOnyv16J1Ivw=	2025-09-03 12:38:04.986121-03	f	admin	Brandon	Rivarola	admin@example.com	CI	0000	f	t	2025-09-03 12:15:32.987744-03	\N
1	pbkdf2_sha256$1000000$8CZjXkHPfB9pPRieXoEZe1$020CX9YgH6xhCaofCG7GHX2A2dtXp0XKYSO2p5kz2bQ=	2025-09-03 12:26:56.50529-03	f	brandonariel98	Brandon Ariel	Rivarola Valenzuela	losrivarola612@gmail.com	CI	4808795	f	t	2025-09-03 12:12:48.517303-03	\N
\.


--
-- Data for Name: usuarios_clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios_clientes (id, created_at, cliente_id, usuario_id) FROM stdin;
3	2025-09-03 12:45:38.297924-03	1	1
\.


--
-- Data for Name: usuarios_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios_groups (id, usuario_id, group_id) FROM stdin;
1	2	3
2	3	5
3	3	4
4	4	2
5	1	1
\.

--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 5, true);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 30, true);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 25, true);


--
-- Name: clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.clientes_id_seq', 1, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 9, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 20, true);


--
-- Name: monedas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.monedas_id_seq', 3, true);


--
-- Name: usuarios_clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_clientes_id_seq', 3, true);


--
-- Name: usuarios_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_groups_id_seq', 14, true);


--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_id_seq', 4, true);


--
-- Name: usuarios_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.usuarios_user_permissions_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

