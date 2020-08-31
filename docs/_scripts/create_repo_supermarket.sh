pulp_http --body POST $BASE_ADDR/pulp/api/v3/repositories/cookbook/cookbook/ name=supermarket description="Snapshots of Supermarket (using lazy download)" remote=$REMOTE_HREF
export REPO_HREF=$(http $BASE_ADDR/pulp/api/v3/repositories/cookbook/cookbook/?name=supermarket | jq -r '.results[0].pulp_href')
