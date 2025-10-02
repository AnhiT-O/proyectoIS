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

COPY public.clientes (nombre, "tipoDocCliente", "docCliente", "correoElecCliente", telefono, "tipoCliente", direccion, ocupacion, declaracion_jurada, segmento, id_stripe, consumo_diario, consumo_mensual, ultimo_consumo, created_at) FROM stdin;
Juan Pérez	CI	1231231	juanperez@example.com	0981123123	F	Asunción, Paraguay	Estudiante	t	minorista	cus_T6oluR2pptn5i1	0	0	2025-09-20	2025-09-20 12:26:10.67909-03
Lucía Gómez	CI	2342342	lucia.gomez@example.com	0982342342	F	Encarnación, Paraguay	Ingeniera	t	minorista	\N	0	0	2025-09-20	2025-09-20 12:27:38.687681-03
Carlos Ramírez	RUC	3453453	carlos_ramirez@example.com	0983453453	F	Ciudad del Este, Paraguay	Comerciante	t	minorista	\N	0	0	2025-09-20	2025-09-20 12:29:50.697586-03
Ana Fernández	CI	4564564	ana.fernandez@example.com	0984564564	F	San Lorenzo, Paraguay	Abogada	t	vip	\N	0	0	2025-09-20	2025-09-20 12:30:54.408672-03
Miguel Torres	CI	5675675	miguel.torres@example.com	0985675675	F	Luque, Paraguay	Contador	t	minorista	\N	0	0	2025-09-20	2025-09-20 12:31:53.579782-03
Sofía Martínez	RUC	6786786	sofia.martinez@example.com	0986786786	F	Capiatá, Paraguay	Médica	t	vip	\N	0	0	2025-09-20	2025-09-20 12:33:32.910055-03
Diego Alonso	CI	7897897	diego.alonso@example.com	0987897897	F	Fernando de la Mora, Paraguay	Arquitecto	t	minorista	\N	0	0	2025-09-20	2025-09-20 12:34:33.754898-03
Valentina Rivas	CI	8908908	valentina.rivas@example.com	0988908908	F	Lambaré, Paraguay	Diseñadora	t	corporativo	\N	0	0	2025-09-20	2025-09-20 12:35:39.80619-03
Camila Acosta	RUC	1234567	camila_acosta@example.com	0981234567	F	Areguá, Paraguay	Psicóloga	t	vip	\N	0	0	2025-09-20	2025-09-20 12:36:39.958919-03
Empresa S.A.	RUC	3456789	empresa@example.com	021456789	J	Asunción, Paraguay	Venta de artículos	t	corporativo	\N	0	0	2025-09-20	2025-09-20 12:38:01.427257-03
\.

COPY public.cuenta_bancaria (banco, numero_cuenta, nombre_titular, nro_documento, cliente_id) FROM stdin;
Banco Atlas	593406	Juan Pérez	1231231	1
Banco Familiar	39784	Juan Pérez	1231231	1
ueno bank	969643	Juan Pérez	1231231	1
Banco Basa	426868	Carlos Ramírez	3453453	3
Cooperativa Universitaria	32329	Ana Fernández	4564564	4
Banco Itaú	753971	Ubaldo Torres	543420	5
Banco Familiar	254591	Camila Acosta	1234567	9
ueno bank	783750	Empresa S.A.	3456789	10
\.

--
-- Data for Name: monedas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monedas (nombre, simbolo, activa, tasa_base, comision_compra, comision_venta, decimales, fecha_cotizacion, denominaciones, stock) FROM stdin;
Euro	EUR	t	8600	200	250	3	2025-09-20 12:19:13.542976-03	{5,10,20,50,100,200,500}	1000000
Real	BRL	t	1340	25	20	3	2025-09-20 12:21:35.90483-03	{2,5,10,20,50,100,200}	10000000
Peso argentino	ARP	t	5	1	0	0	2025-09-20 12:22:28.974217-03	{10,20,50,100,200,500,1000,2000,10000,20000}	100000000
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.roles (group_ptr_id, descripcion) FROM stdin;
4	Rol encargado de bloquear o desbloquear usuarios del sistema.
5	Rol encargado de gestionar y asignar clientes a usuarios.
\.


--
-- Data for Name: usuarios; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios (password, last_login, is_superuser, username, first_name, last_name, email, tipo_documento, numero_documento, bloqueado, is_active, date_joined, cliente_activo_id) FROM stdin;
pbkdf2_sha256$1000000$wJrbuxT7jPkLSdYMPimfRK$tizTqXuQhLznLeqdwJdLOXMyzYnWNnBQoacwLhnT/iY=	\N	f	iris	Iris María	Mendoza Ortiz	iris@example.com	CI	6841885	f	t	2025-09-20 12:41:57.196011-03	\N
pbkdf2_sha256$1000000$nDM0sJaQBiMzsduSi21c8E$v7g5eQiQWgQigZTXYsrOtJPCkbqc6k6fuz/7I1SZHcQ=	\N	f	anahi	Claudia Anahi	Talavera Ovelar	anahi@example.com	CI	5461535	f	t	2025-09-20 12:56:06.05157-03	\N
pbkdf2_sha256$1000000$qzR2qkBvl5Q7MAobJuW6Qv$rkCiLwrpvnd+xMbCm2BkoiW1y+LyIlG40Ezfv69nsEM=	\N	f	aylen	Aylén María	Wyder Aquino	aylen@example.com	CI	5130314	f	t	2025-09-20 12:49:11.68885-03	\N
pbkdf2_sha256$1000000$7dwyrYsJpRzVekudU6YBRJ$jx0XESJXTmJKuHc1V5io4pq5mi03X9FpGNRCUl1shzw=	2025-09-20 15:02:43.434869-03	f	josias	Josias David	Espínola Nuñez	josias@example.com	CI	5167191	f	t	2025-09-20 12:56:51.22464-03	1
pbkdf2_sha256$1000000$8an91M8C8wOOfTvVxeLPkk$SqNaJcNTLiznTfzsbKi8T0KIZ7hgbO+N7Px1+xAetkA=	2025-09-20 15:04:20.553559-03	f	admin	Brandon	Rivarola	admin@example.com	CI	4808795	f	t	2025-09-20 12:11:14.859291-03	\N
\.


--
-- Data for Name: usuarios_clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes_usuarios (cliente_id, usuario_id) FROM stdin;
4	4
7	4
1	4
5	4
6	4
4	2
3	2
7	2
10	2
6	2
\.


--
-- Data for Name: usuarios_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.usuarios_groups (usuario_id, group_id) FROM stdin;
5	3
3	2
2	1
1	5
1	4
4	1
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

