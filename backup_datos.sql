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
2	25
2	23
5	18
5	20
4	17
\.


--
-- Data for Name: clientes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.clientes (nombre, tipo_documento, numero_documento, correo_electronico, telefono, tipo, direccion, ocupacion, declaracion_jurada, segmento, id_stripe, consumo_diario, consumo_mensual, ultimo_consumo) FROM stdin;
Juan Pérez	CI	1231231	juanperez@example.com	0981123123	F	Asunción, Paraguay	Estudiante	t	minorista	cus_T6oluR2pptn5i1	0	0	2025-09-20
Lucía Gómez	CI	2342342	lucia.gomez@example.com	0982342342	F	Encarnación, Paraguay	Ingeniera	t	minorista	\N	0	0	2025-09-20
Carlos Ramírez	RUC	3453453	carlos_ramirez@example.com	0983453453	F	Ciudad del Este, Paraguay	Comerciante	t	minorista	\N	0	0	2025-09-20
Ana Fernández	CI	4564564	ana.fernandez@example.com	0984564564	F	San Lorenzo, Paraguay	Abogada	t	vip	\N	0	0	2025-09-20
Miguel Torres	CI	5675675	miguel.torres@example.com	0985675675	F	Luque, Paraguay	Contador	t	minorista	\N	0	0	2025-09-20
Sofía Martínez	RUC	6786786	sofia.martinez@example.com	0986786786	F	Capiatá, Paraguay	Médica	t	vip	\N	0	0	2025-09-20
Diego Alonso	CI	7897897	diego.alonso@example.com	0987897897	F	Fernando de la Mora, Paraguay	Arquitecto	t	minorista	\N	0	0	2025-09-20
Valentina Rivas	CI	8908908	valentina.rivas@example.com	0988908908	F	Lambaré, Paraguay	Diseñadora	t	corporativo	\N	0	0	2025-09-20
Camila Acosta	RUC	1234567	camila_acosta@example.com	0981234567	F	Areguá, Paraguay	Psicóloga	t	vip	\N	0	0	2025-09-20
Empresa S.A.	RUC	3456789	empresa@example.com	021456789	J	Asunción, Paraguay	Venta de artículos	t	corporativo	\N	0	0	2025-09-20
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

COPY public.billetera (nombre_titular, nro_documento, tipo_billetera, telefono, cliente_id) FROM stdin;
Juan Pérez	1231231	Tigo Money	0981123123	1
Juan Pérez	1231231	Zimple	0981123123	1
Sofía Martínez	6786786	Billetera Personal	0986786786	6
Valentina Rivas	8908908	Tigo Money	0988908908	8
\.

--
-- Data for Name: monedas; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.monedas (nombre, simbolo, activa, tasa_base, comision_compra, comision_venta, decimales, fecha_cotizacion) FROM stdin;
Euro	EUR	t	8500	200	150	2	2025-10-10 10:50:00
Real	BRL	t	1310	20	30	2	2025-10-10 10:50:00
Peso argentino	ARP	t	5	1	0	0	2025-10-10 10:50:00
\.


COPY public.denominaciones (valor, moneda_id) FROM stdin;
5	2
10	2
20	2
50	2
100	2
200	2
500	2
2	3
5	3
10	3
20	3
50	3
100	3
200	3
10	4
20	4
50	4
100	4
200	4
500	4
1000	4
2000	4
10000	4
20000	4
\.

COPY public.tausers (puerto) FROM stdin;
8001
8002
8003
8004
8005
\.

COPY public.billetes_tauser (tauser_id, denominacion_id, cantidad) FROM stdin;
1	1	100
1	2	100
1	2	100
1	3	100
1	4	100
1	5	100
1	6	100
1	7	100
1	8	100
1	9	100
1	10	100
1	11	100
1	12	100
1	13	100
1	14	100
1	15	100
1	16	100
1	17	100
1	18	100
1	19	100
1	20	100
1	21	100
1	22	100
1	23	100
1	24	100
1	25	100
1	26	100
1	27	100
1	28	100
1	29	100
1	30	100
1	31	100
1	32	100
1	33	100
1	34	100
1	35	100
1	36	100
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

COPY public.usuarios (password, last_login, is_superuser, username, first_name, last_name, email, telefono, numero_documento, bloqueado, is_active, date_joined, cliente_activo_id) FROM stdin;
pbkdf2_sha256$1000000$wJrbuxT7jPkLSdYMPimfRK$tizTqXuQhLznLeqdwJdLOXMyzYnWNnBQoacwLhnT/iY=	\N	f	iris	Iris María	Mendoza Ortiz	irismendoza012@fpuna.edu.py	0984552373	6841885	f	t	2025-09-20 12:41:57.196011-03	\N
pbkdf2_sha256$1000000$nDM0sJaQBiMzsduSi21c8E$v7g5eQiQWgQigZTXYsrOtJPCkbqc6k6fuz/7I1SZHcQ=	\N	f	anahi	Claudia Anahi	Talavera Ovelar	clautalavera12@fpuna.edu.py	0972158149	5461535	f	t	2025-09-20 12:56:06.05157-03	\N
pbkdf2_sha256$1000000$qzR2qkBvl5Q7MAobJuW6Qv$rkCiLwrpvnd+xMbCm2BkoiW1y+LyIlG40Ezfv69nsEM=	\N	f	aylen	Aylén María	Wyder Aquino	aylen14wyder@fpuna.edu.py	0986743708	5130314	f	t	2025-09-20 12:49:11.68885-03	\N
pbkdf2_sha256$1000000$7dwyrYsJpRzVekudU6YBRJ$jx0XESJXTmJKuHc1V5io4pq5mi03X9FpGNRCUl1shzw=	2025-09-20 15:02:43.434869-03	f	josias	Josias David	Espínola Nuñez	totiespinola@fpuna.edu.py	0982977328	5167191	f	t	2025-09-20 12:56:51.22464-03	1
pbkdf2_sha256$1000000$8an91M8C8wOOfTvVxeLPkk$SqNaJcNTLiznTfzsbKi8T0KIZ7hgbO+N7Px1+xAetkA=	2025-09-20 15:04:20.553559-03	f	admin	Brandon	Rivarola	losrivarola612@fpuna.edu.py	0981458383	4808795	f	t	2025-09-20 12:11:14.859291-03	\N
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

