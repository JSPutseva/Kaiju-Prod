-- Seeds quarter_resources with the real "Initial distribution" table from
-- the Kaiju rules doc (page 4). available_quantity = initial_quantity and
-- reserved_quantity = 0 since nothing has been reserved/transferred yet.
INSERT INTO quarter_resources (quarter_id, resource_type_id, initial_quantity, available_quantity, reserved_quantity)
SELECT q.id, rt.id, v.initial_quantity, v.initial_quantity, 0
FROM (VALUES
    ('Apex',   'Medical personnel',       12),
    ('Echo',   'Medical personnel',        5),
    ('Warden', 'Medical personnel',        8),
    ('Xeno',   'Medical personnel',        3),
    ('Zion',   'Medical personnel',        7),

    ('Apex',   'Rescue teams',              4),
    ('Echo',   'Rescue teams',              9),
    ('Warden', 'Rescue teams',              3),
    ('Xeno',   'Rescue teams',              6),
    ('Zion',   'Rescue teams',              5),

    ('Apex',   'Transport vehicles',        6),
    ('Echo',   'Transport vehicles',        3),
    ('Warden', 'Transport vehicles',       10),
    ('Xeno',   'Transport vehicles',        4),
    ('Zion',   'Transport vehicles',        7),

    ('Apex',   'Emergency shelters',        8),
    ('Echo',   'Emergency shelters',        6),
    ('Warden', 'Emergency shelters',        4),
    ('Xeno',   'Emergency shelters',       10),
    ('Zion',   'Emergency shelters',        2),

    ('Apex',   'Food & water supplies',     5),
    ('Echo',   'Food & water supplies',     8),
    ('Warden', 'Food & water supplies',     6),
    ('Xeno',   'Food & water supplies',     7),
    ('Zion',   'Food & water supplies',     9),

    ('Apex',   'Communication equipment',   3),
    ('Echo',   'Communication equipment',   7),
    ('Warden', 'Communication equipment',   5),
    ('Xeno',   'Communication equipment',   8),
    ('Zion',   'Communication equipment',   4),

    ('Apex',   'Power generators',          7),
    ('Echo',   'Power generators',          2),
    ('Warden', 'Power generators',          9),
    ('Xeno',   'Power generators',          5),
    ('Zion',   'Power generators',          6),

    ('Apex',   'Engineering crews',         2),
    ('Echo',   'Engineering crews',         6),
    ('Warden', 'Engineering crews',         7),
    ('Xeno',   'Engineering crews',         4),
    ('Zion',   'Engineering crews',         8),

    ('Apex',   'Security units',            9),
    ('Echo',   'Security units',            4),
    ('Warden', 'Security units',            2),
    ('Xeno',   'Security units',            6),
    ('Zion',   'Security units',            3),

    ('Apex',   'Hazmat equipment',          3),
    ('Echo',   'Hazmat equipment',          5),
    ('Warden', 'Hazmat equipment',          4),
    ('Xeno',   'Hazmat equipment',          2),
    ('Zion',   'Hazmat equipment',         10)
) AS v(quarter_name, resource_name, initial_quantity)
JOIN quarters q ON q.name = v.quarter_name
JOIN resource_types rt ON rt.name = v.resource_name;
