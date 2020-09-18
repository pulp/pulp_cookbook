pulp_http --body POST $BASE_ADDR/pulp/api/v3/repositories/cookbook/cookbook/ name=foo
export REPO_HREF=$(http $BASE_ADDR/pulp/api/v3/repositories/cookbook/cookbook/?name=foo | jq -r '.results[0].pulp_href')
