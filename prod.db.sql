
--
-- Data for Name: companies; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO companies (name, website, address, notes) VALUES ('DigiKey', 'www.digikey.com', '701 Brooks Avenue South,
Thief River Falls, MN 56701 USA', 'World''s Largest Selection
of Electronic Components Available for Immediate Shipment!®');
INSERT INTO companies (name, website, address, notes) VALUES ('McMaster-Carr', 'www.mcmaster.com', '9630 Norwalk Blvd.
Santa Fe Springs, CA 90670-2932', 'From washers to jib cranes');
INSERT INTO companies (name, website, address, notes) VALUES ('Advanced Circuits', 'www.4pcb.com', '21101 E. 32nd Pkwy.
Aurora, CO 80011', 'Fuill service PCB manufacturing');
INSERT INTO companies (name, website, address, notes) VALUES ('All-Spec', 'www.all-spec.com', '5228 US Hwy 421 N.
Wilmington, NC 28401', 'Cleanroom and lab equipment');
INSERT INTO companies (name, website, address, notes) VALUES ('Allied Wire and Cable', 'www.awcwire.com	', '101 Kestrel Drive
Collegeville, PA 19426', 'Keepin'' it reel since 1988!');
INSERT INTO companies (name, website, address, notes) VALUES ('NewEgg', 'www.newegg.com', '9997 Rose Hills Road Whittier, CA. 90601', 'Everything computers');
INSERT INTO companies (name, website, address, notes) VALUES ('Proto Labs', 'https://www.protolabs.com/', ' 5540 Pioneer Creek Dr., Maple Plain, MN 55359 USA', 'PRI Acct# 82468	');
INSERT INTO companies (name, website, address, notes) VALUES ('Western Tool', 'www.westerntool.com', '10840 Harney Street
Omaha, NE 68154-2638', 'Shop tools');
INSERT INTO companies (name, website, address, notes) VALUES ('Jackson Spring', 'http://www.jacksonspring.com', '299 Bond St.
Elk Grove Village, Il 60007', 'Good for custom springs');
INSERT INTO companies (name, website, address, notes) VALUES ('ModelWerks', 'http://www.modelwerks.com/', '655 South Andover
Seattle, WA  98108', 'Good for quick turn-around');

--
-- Data for Name: criticalities; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO criticalities (name, description) VALUES ('ODD', 'Something mildly strange happened');
INSERT INTO criticalities (name, description) VALUES ('WORRISOME', 'Something strange happened that is going to bug you until you figure out what it was');
INSERT INTO criticalities (name, description) VALUES ('SERIOUS', 'Something bad happened that needs to be addressed immediately');
INSERT INTO criticalities (name, description) VALUES ('SoF', 'Shit''s on Fire.  Stop whatever else is happening and fix this now.');

--
-- Data for Name: dispositions; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO dispositions (name, description) VALUES ('REWORK', 'Fix it.');
INSERT INTO dispositions (name, description) VALUES ('LU', 'Limited Use');
INSERT INTO dispositions (name, description) VALUES ('FIFI', 'Fuck it, fly it (use as-is)');
INSERT INTO dispositions (name, description) VALUES ('SCRAP', 'Permanently alter it so there''s no chance of it being used');

--
-- Data for Name: hardware_types; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO hardware_types (name, description) VALUES ('FLIGHT', 'Hardware that represents Planetary Resources -  built and tracked with the care and pedigree required for flight and/or delivery as a PRI product.');
INSERT INTO hardware_types (name, description) VALUES ('EM / NON-FLIGHT', 'Identical to Flight hardware but specifically intended for ground-based use/testing only');
INSERT INTO hardware_types (name, description) VALUES ('DEVELOPMENTAL', 'Not intended to be or represent Flight hardware but is inteneded to inform the development/design of Flight hardware');
INSERT INTO hardware_types (name, description) VALUES ('GSE', 'Fixturing or other tooling designed to interact with and support the manufacture / build / test / transportation / etc. of Flight hardware');
INSERT INTO hardware_types (name, description) VALUES ('EQUIPMENT', 'Infrastructure, tools, test equipment, etc. used at PRI for product development (oscilloscopes, thermal chambers, CNC mills, etc.)');
INSERT INTO hardware_types (name, description) VALUES ('MISC', 'Truly random stuff - tap handles and JIRA horse rear-end awards.');

--
-- Data for Name: materials; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO materials (name, description) VALUES ('ALUMINUM 6061-T6', '');
INSERT INTO materials (name, description) VALUES ('ALUMINUM 7075-T7', '*Do NOT* anodize Type II');
INSERT INTO materials (name, description) VALUES ('ALUMINUM 7050-T7', '');
INSERT INTO materials (name, description) VALUES ('TITANIUM 6Al-4V', '');
INSERT INTO materials (name, description) VALUES ('TITANIUM 6Al-4V STA', '');
INSERT INTO materials (name, description) VALUES ('INCONEL 718', '');
INSERT INTO materials (name, description) VALUES ('15-5PH H1025', '');
INSERT INTO materials (name, description) VALUES ('15-5PH H1150', '');
INSERT INTO materials (name, description) VALUES ('17-4PH H1150', '');
INSERT INTO materials (name, description) VALUES ('DELRIN', '');
INSERT INTO materials (name, description) VALUES ('ULTEM 2300', '');
INSERT INTO materials (name, description) VALUES ('ALLOY STEEL', '');
INSERT INTO materials (name, description) VALUES ('DACRON', '');

--
-- Data for Name: material_specifications; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4025', 1);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4026', 1);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4027', 1);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS-QQ-A-250/11', 1);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4150', 1);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4078', 2);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS-QQ-A-250/12', 2);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4050', 3);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4108', 3);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 4911', 4);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS-T-9046', 4);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS-T-9046', 5);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5664', 6);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5659', 7);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5862', 7);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5659', 8);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5862', 8);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5604', 9);
INSERT INTO material_specifications (name, material_id) VALUES ('AMS 5643', 9);

--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: pid_user
--
INSERT INTO projects (name, description) VALUES ('24 - Arkyd-6', '');
INSERT INTO projects (name, description) VALUES ('28 - Arkyd-100', '');
INSERT INTO projects (name, description) VALUES ('29 - Arkyd-200', '');
INSERT INTO projects (name, description) VALUES ('32 - NEO Targeting', '');
INSERT INTO projects (name, description) VALUES ('33 - PID', '');
