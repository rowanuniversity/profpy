create table rowan.fauxrm_test_general_names (
  id         number GENERATED BY DEFAULT ON NULL AS IDENTITY PRIMARY KEY NOT NULL,
  first_name varchar2(255),
  last_name  varchar2(255)
)