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
Euro	EUR	t	7900	500	250	2	2025-11-21 09:36:00
Real	BRL	t	1320	40	20	2	2025-11-21 09:37:00
Peso argentino	ARP	t	5	1	1	0	2025-10-10 10:50:00
\.

COPY public.historial_cotizaciones (nombre_moneda, fecha, tasa_base, comision_compra, comision_venta, precio_compra, precio_venta, fecha_registro, moneda_id) FROM stdin;
Euro	2025-10-10	8500	200	150	8300	8650	2025-10-10 10:50:00	2
Real	2025-10-10	1310	20	30	1290	1340	2025-10-10 10:50:00	3
Peso argentino	2025-10-10	5	1	1	4	6	2025-10-10 10:50:00	4
Dólar estadounidense	2025-10-17	7000	30	70	6970	7070	2025-10-17 14:35:00	1
Real	2025-10-17	1300	40	40	1260	1340	2025-10-17 14:35:00	3
Dólar estadounidense	2025-10-18	7000	40	60	6960	7060	2025-10-18 19:21:00	1
Euro	2025-10-18	8500	300	150	8200	8650	2025-10-18 19:22:00	2
Euro	2025-10-22	8500	300	100	8200	8600	2025-10-22 15:41:00	2
Real	2025-10-22	1300	20	40	1280	1340	2025-10-22 15:42:00	3
Dólar estadounidense	2025-10-22	7030	30	40	7000	7070	2025-10-22 15:43:00	1
Euro	2025-10-22	8500	350	50	8150	8550	2025-10-22 15:41:00	2
Dólar estadounidense	2025-10-23	7030	30	30	7000	7060	2025-10-23 15:00:00	1
Real	2025-10-28	1300	20	30	1280	1330	2025-10-28 13:10:00	3
Euro	2025-10-28	8300	200	100	8150	8550	2025-10-28 13:10:00	2
Dólar estadounidense	2025-10-28	7030	30	40	7000	7070	2025-10-28 13:10:00	1
Euro	2025-11-01	8300	300	100	8000	8400	2025-11-01 12:30:00	2
Real	2025-11-01	1300	30	20	1270	1320	2025-11-01 12:30:00	3
Dólar estadounidense	2025-11-01	7030	30	50	7000	7080	2025-11-01 12:30:00	1
Euro	2025-11-06	8100	250	200	7850	8300	2025-11-06 10:30:00	2
Real	2025-11-06	1300	15	40	1285	1340	2025-11-06 10:30:00	3
Dólar estadounidense	2025-11-06	7030	30	30	7000	7060	2025-11-06 10:30:00	1
Euro	2025-11-14	7900	250	300	7650	8200	2025-11-14 11:41:00	2
Real	2025-11-14	1320	30	30	1290	1350	2025-11-14 11:42:00	3
Dólar estadounidense	2025-11-14	7000	60	40	6940	7040	2025-11-14 11:40:00	1
Euro	2025-11-21	7900	500	250	7400	8150	2025-11-21 09:36:00	2
Real	2025-11-21	1320	40	20	1280	1340	2025-11-21 09:37:00	3
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

COPY public.tausers (puerto, sucursal) FROM stdin;
8001	Asunción
8002	San Lorenzo
8003	Fernando de la Mora
8004	Ñemby
8005	Luque
\.

COPY public.billetes_tauser (tauser_id, denominacion_id, cantidad) FROM stdin;
1	1	100
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

COPY public.roles (group_ptr_id, descripcion) FROM stdin;
4	Rol encargado de bloquear o desbloquear usuarios del sistema.
5	Rol encargado de gestionar y asignar clientes a usuarios.
\.


COPY public.usuarios (password, last_login, is_superuser, username, first_name, last_name, email, telefono, numero_documento, bloqueado, is_active, date_joined, cliente_activo_id) FROM stdin;
pbkdf2_sha256$1000000$wJrbuxT7jPkLSdYMPimfRK$tizTqXuQhLznLeqdwJdLOXMyzYnWNnBQoacwLhnT/iY=	\N	f	iris	Iris María	Mendoza Ortiz	irismendoza012@fpuna.edu.py	0984552373	6841885	f	t	2025-09-20 12:41:57.196011-03	\N
pbkdf2_sha256$1000000$nDM0sJaQBiMzsduSi21c8E$v7g5eQiQWgQigZTXYsrOtJPCkbqc6k6fuz/7I1SZHcQ=	\N	f	anahi	Claudia Anahi	Talavera Ovelar	clautalavera12@fpuna.edu.py	0972158149	5461535	f	t	2025-09-20 12:56:06.05157-03	\N
pbkdf2_sha256$1000000$qzR2qkBvl5Q7MAobJuW6Qv$rkCiLwrpvnd+xMbCm2BkoiW1y+LyIlG40Ezfv69nsEM=	\N	f	aylen	Aylén María	Wyder Aquino	aylen14wyder@fpuna.edu.py	0986743708	5130314	f	t	2025-09-20 12:49:11.68885-03	\N
pbkdf2_sha256$1000000$7dwyrYsJpRzVekudU6YBRJ$jx0XESJXTmJKuHc1V5io4pq5mi03X9FpGNRCUl1shzw=	2025-09-20 15:02:43.434869-03	f	josias	Josias David	Espínola Nuñez	totiespinola@fpuna.edu.py	0982977328	5167191	f	t	2025-09-20 12:56:51.22464-03	1
pbkdf2_sha256$1000000$8an91M8C8wOOfTvVxeLPkk$SqNaJcNTLiznTfzsbKi8T0KIZ7hgbO+N7Px1+xAetkA=	2025-09-20 15:04:20.553559-03	f	admin	Brandon	Rivarola	losrivarola612@fpuna.edu.py	0981458383	4808795	f	t	2025-09-20 12:11:14.859291-03	\N
\.

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


COPY public.usuarios_groups (usuario_id, group_id) FROM stdin;
5	3
3	2
2	1
1	5
1	4
4	1
\.

COPY public.transacciones (tipo, monto, cotizacion, precio_base, beneficio_segmento, porc_beneficio_segmento, recargo_pago, porc_recargo_pago, recargo_cobro, porc_recargo_cobro, precio_final, pagado, medio_pago, medio_cobro, fecha_hora, estado, razon, token, factura, numero_factura, cliente_id, moneda_id, usuario_id) FROM stdin;
venta	500	6930	3465000	0	0%	35000	1.0%	0	0%	3430000	3430000	Tarjeta de Crédito (**** **** **** 4242)	Cuenta bancaria - Banco Atlas (593406)	2025-11-21 09:58:56.36467-03	Completa	\N	\N	\N	\N	1	1	4
compra	800	7070	5656000	0	0%	0	0%	0	0%	5656000	5656000	Efectivo	Efectivo	2025-09-15 10:30:00-03	Completa	\N	\N	\N	\N	1	1	4
venta	650	6930	4504500	0	0%	45500	1.0%	0	0%	4459000	4459000	Tarjeta de Crédito (**** **** **** 1234)	Cuenta bancaria - Banco Familiar (39784)	2025-09-20 14:20:00-03	Completa	\N	\N	\N	\N	1	1	4
compra	1200	8650	10380000	0	0%	155700	1.5%	0	0%	10535700	10535700	Tarjeta de Crédito (**** **** **** 5678)	Efectivo	2025-09-25 11:15:00-03	Completa	\N	\N	\N	\N	3	2	4
venta	1000	6930	6930000	0	0%	138600	2.0%	0	0%	6791400	6791400	Billetera Electrónica - Tigo Money (0981123123)	Transferencia bancaria - Banco Atlas (593406)	2025-10-05 09:45:00-03	Completa	\N	\N	\N	\N	1	1	4
compra	450	7070	3181500	318150	10%	0	0%	0	0%	2863350	2863350	Efectivo	Efectivo	2025-10-10 16:30:00-03	Completa	\N	\N	\N	\N	4	1	4
venta	850	7900	6715000	671500	10%	0	0%	0	0%	6043500	6043500	Efectivo	Cuenta bancaria - Cooperativa Universitaria (32329)	2025-10-15 13:00:00-03	Completa	\N	\N	\N	\N	4	2	4
compra	2500	1340	3350000	0	0%	33833	1.0%	0	0%	3383833	3383833	Tarjeta de Crédito (**** **** **** 9876)	Efectivo	2025-10-20 10:00:00-03	Completa	\N	\N	\N	\N	3	3	4
venta	700	6930	4851000	0	0%	0	0%	0	0%	4851000	4851000	Transferencia bancaria - Banco Basa (426868)	Cuenta bancaria - Banco Basa (426868)	2025-10-25 15:20:00-03	Completa	\N	\N	\N	\N	3	1	4
compra	950	8300	7885000	788500	10%	0	0%	0	0%	7096500	7096500	Efectivo	Efectivo	2025-11-01 11:30:00-03	Completa	\N	\N	\N	\N	6	2	4
venta	1800	1280	2304000	230400	10%	0	0%	0	0%	2073600	2073600	Efectivo	Transferencia bancaria - Banco Familiar (254591)	2025-11-05 14:45:00-03	Completa	\N	\N	\N	\N	9	3	4
compra	3500	7060	24710000	1235500	5%	0	0%	0	0%	23474500	23474500	Transferencia bancaria - ueno bank (783750)	Efectivo	2025-11-10 09:00:00-03	Completa	\N	\N	\N	\N	10	1	4
venta	2000	6940	13880000	694000	5%	0	0%	0	0%	13186000	13186000	Efectivo	Transferencia bancaria - ueno bank (783750)	2025-11-12 16:15:00-03	Completa	\N	\N	\N	\N	10	1	4
compra	1100	7060	7766000	0	0%	232980	3.0%	0	0%	7998980	7998980	Billetera Electrónica - Zimple (0981123123)	Efectivo	2025-11-15 10:30:00-03	Completa	\N	\N	\N	\N	1	1	4
venta	750	7400	5550000	555000	10%	0	0%	0	0%	4995000	4995000	Efectivo	Cuenta bancaria - Cooperativa Universitaria (32329)	2025-11-18 13:20:00-03	Completa	\N	\N	\N	\N	4	2	4
compra	1500	1340	2010000	100500	5%	0	0%	0	0%	1909500	1909500	Efectivo	Efectivo	2025-11-20 11:00:00-03	Completa	\N	\N	\N	\N	8	3	4
venta	900	1280	1152000	57600	5%	0	0%	0	0%	1094400	1094400	Efectivo	Transferencia bancaria - ueno bank (969643)	2025-11-22 15:45:00-03	Completa	\N	\N	\N	\N	1	3	4
compra	550	8150	4482500	448250	10%	0	0%	0	0%	4034250	4034250	Efectivo	Efectivo	2025-11-25 10:15:00-03	Completa	\N	\N	\N	\N	6	2	4
venta	850	6930	5890500	0	0%	88358	1.5%	0	0%	5802142	5802142	Tarjeta de Crédito (**** **** **** 4321)	Cuenta bancaria - Banco Atlas (593406)	2025-11-26 09:30:00-03	Completa	\N	\N	\N	\N	1	1	4
compra	2200	7060	15532000	776600	5%	0	0%	0	0%	14755400	14755400	Transferencia bancaria - ueno bank (783750)	Efectivo	2025-11-28 08:00:00-03	Completa	\N	\N	\N	\N	10	1	4
venta	1200	6930	8316000	0	0%	83160	1.0%	0	0%	8232840	8232840	Tarjeta de Crédito (**** **** **** 8888)	Cuenta bancaria - Banco Familiar (39784)	2025-11-28 11:30:00-03	Completa	\N	\N	\N	\N	1	1	4
compra	700	8150	5705000	570500	10%	0	0%	0	0%	5134500	5134500	Efectivo	Efectivo	2025-11-28 14:45:00-03	Completa	\N	\N	\N	\N	4	2	4
venta	1600	1280	2048000	102400	5%	0	0%	0	0%	1945600	1945600	Efectivo	Cuenta bancaria - Banco Basa (426868)	2025-11-28 17:20:00-03	Completa	\N	\N	\N	\N	8	3	4
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

