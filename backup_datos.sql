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

COPY public.auth_group (name) FROM stdin;
Moderador de usuarios
Encargado de clientes
\.

--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (group_id, permission_id) FROM stdin;
2	24
2	23
5	18
5	20
4	17
\.


--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (nombre, "tipoDocCliente", "docCliente", "correoElecCliente", telefono, "tipoCliente", direccion, ocupacion, declaracion_jurada, segmento, beneficio_segmento, created_at, updated_at) FROM stdin;
Juan Pérez	CI	1231231	juanperez@example.com	0981123123	F	Asunción, Paraguay	Estudiante	t	minorista	0	2025-09-03 12:36:01.401701-03	2025-09-03 12:38:32.291502-03
Lucía Gómez	CI	2342342	lucia.gomez@example.com	0982342342	F	Encarnación, Paraguay	Ingeniera	t	minorista	0	2025-09-03 12:39:01.401701-03	2025-09-03 12:40:32.291502-03
Carlos Ramírez	RUC	3453453	carlos.ramirez@example.com	0983453453	F	Ciudad del Este, Paraguay	Comerciante	f	minorista	0	2025-09-03 12:41:01.401701-03	2025-09-03 12:42:32.291502-03
Ana Fernández	CI	4564564	ana.fernandez@example.com	0984564564	F	San Lorenzo, Paraguay	Abogada	t	vip	10	2025-09-03 12:43:01.401701-03	2025-09-03 12:44:32.291502-03
Miguel Torres	CI	5675675	miguel.torres@example.com	0985675675	F	Luque, Paraguay	Contador	t	minorista	0	2025-09-03 12:45:01.401701-03	2025-09-03 12:46:32.291502-03
Sofía Martínez	RUC	6786786	sofia.martinez@example.com	0986786786	F	Capiatá, Paraguay	Médica	f	vip	10	2025-09-03 12:47:01.401701-03	2025-09-03 12:48:32.291502-03
Diego Alonso	CI	7897897	diego.alonso@example.com	0987897897	F	Fernando de la Mora, Paraguay	Arquitecto	t	minorista	0	2025-09-03 12:49:01.401701-03	2025-09-03 12:50:32.291502-03
Valentina Rivas	CI	8908908	valentina.rivas@example.com	0988908908	F	Lambaré, Paraguay	Diseñadora	t	corporativo	5	2025-09-03 12:51:01.401701-03	2025-09-03 12:52:32.291502-03
Javier Benítez	CI	9019019	javier.benitez@example.com	0989019019	F	Villa Elisa, Paraguay	Programador	t	minorista	0	2025-09-03 12:53:01.401701-03	2025-09-03 12:54:32.291502-03
Camila Acosta	RUC	1234567	camila.acosta@example.com	0981234567	F	Areguá, Paraguay	Psicóloga	t	vip	10	2025-09-03 12:55:01.401701-03	2025-09-03 12:56:32.291502-03
Pedro Vera	CI	2345678	pedro.vera@example.com	0982345678	F	Itauguá, Paraguay	Chef	t	minorista	0	2025-09-03 12:57:01.401701-03	2025-09-03 12:58:32.291502-03
Empresa S.A.	RUC	3456789	empresa@example.com	0983456789	J	Asunción, Paraguay	Empresa	t	corporativo	5	2025-09-03 12:59:01.401701-03	2025-09-03 13:00:32.291502-03
\.

--
-- Data for Name: monedas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monedas (nombre, simbolo, activa, tasa_base, comision_compra, comision_venta, decimales, fecha_cotizacion) FROM stdin;
Euro	EUR	t	8000	250	300	3	2025-09-10 12:00:00.000000-03
Peso argentino	ARG	t	10	5	7	5	2025-09-10 12:00:00.000000-03
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

COPY public.usuarios (password, last_login, is_superuser, username, first_name, last_name, email, tipo_cedula, cedula_identidad, bloqueado, is_active, date_joined, cliente_activo_id) FROM stdin;
pbkdf2_sha256$1000000$KUtO3Kz9sYyDujs6givUsm$VVkcJj72tGebc5JKVfCC9OcdmKFwxr20mwyo0fYqECU=	2025-09-03 12:33:58.499498-03	f	iris	Iris	Mendoza	iris@example.com	CI	7897897	f	t	2025-09-03 12:26:33.888296-03	\N
pbkdf2_sha256$1000000$nZ5bZGdPP4MeFsTQG0VxIc$NswnhxthPgnIjpC2ub27BMXWi9bdOmR8m/CDLbOwsLM=	2025-09-03 12:37:04.904755-03	f	aylen	Aylen	Wyder	aylen@example.com	CI	4564564	f	t	2025-09-03 12:31:58.921293-03	\N
pbkdf2_sha256$1000000$gG25IPHhpfNHXpI6vKQYCg$1lsAHqYbrXyYWF+DKB6IgNE0sweuyzyfOnyv16J1Ivw=	2025-09-03 12:38:04.986121-03	f	admin	Brandon	Rivarola	admin@example.com	CI	0000	f	t	2025-09-03 12:15:32.987744-03	\N
pbkdf2_sha256$1000000$8CZjXkHPfB9pPRieXoEZe1$020CX9YgH6xhCaofCG7GHX2A2dtXp0XKYSO2p5kz2bQ=	2025-09-03 12:26:56.50529-03	f	brandon	Brandon Ariel	Rivarola Valenzuela	brandon@example.com	CI	4808795	f	t	2025-09-03 12:12:48.517303-03	\N
pbkdf2_sha256$1000000$Ml020x96NUbcZyIAS2SNr5$iOYR5KQce+gBngzT7vhW+r2+qVFhaxfSKAYmi1lraYE=	2025-09-10 09:30:20.317396-03	f	anahi	Anahí	Talavera	anahi@example.com	CI	6138756	f	t	2025-09-10 08:47:36.287984-03	\N
pbkdf2_sha256$1000000$nZ5bZGdPP4MeFsTQG0VxIc$NswnhxthPgnIjpC2ub27BMXWi9bdOmR8m/CDLbOwsLM=	2025-09-10 09:30:56.653747-03	f	josias	Josias	Espinola	josias@example.com	CI	5435341	f	t	2025-09-03 12:31:58.921293-03	\N
\.


--
-- Data for Name: usuarios_clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios_clientes (created_at, cliente_id, usuario_id) FROM stdin;
2025-09-03 12:45:38.297924-03	1	4
2025-09-09 15:32:38.321384-03	10	4
2025-09-09 15:32:38.32894-03	7	4
2025-09-09 15:32:38.33572-03	12	4
2025-09-09 15:32:38.342084-03	2	4
2025-09-10 09:01:52.405966-03	4	6
2025-09-10 09:01:52.414183-03	10	6
2025-09-10 09:01:52.420898-03	3	6
2025-09-10 09:01:52.427215-03	7	6
2025-09-10 09:02:08.30708-03	5	5
2025-09-10 09:02:08.315789-03	11	5
2025-09-10 09:02:08.322134-03	6	5
2025-09-10 09:02:08.328653-03	8	5
\.


--
-- Data for Name: usuarios_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios_groups (usuario_id, group_id) FROM stdin;
3	3
1	5
1	4
2	2
4	1
5	1
6	1
\.

--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.auth_group_id_seq', 5, true);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.auth_permission_id_seq', 25, true);


--
-- Name: clientes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.clientes_id_seq', 1, true);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.django_content_type_id_seq', 9, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.django_migrations_id_seq', 20, true);


--
-- Name: monedas_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.monedas_id_seq', 3, true);



--
-- Name: usuarios_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.usuarios_id_seq', 4, true);


--
-- Name: usuarios_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

-- SELECT pg_catalog.setval('public.usuarios_user_permissions_id_seq', 1, false);


--
-- PostgreSQL database dump complete
--

