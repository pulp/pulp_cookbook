export REPO_HREF=$(http $BASE_ADDR/pulp/api/v3/repositories/cookbook/cookbook/?name=foo | jq -r '.results[0].pulp_href')
export LATEST_VERSION_HREF=$(http $BASE_ADDR$REPO_HREF | jq -r '.latest_version_href')
task_result=$(pulp_http POST $BASE_ADDR/pulp/api/v3/publications/cookbook/cookbook/ repository_version=$LATEST_VERSION_HREF)
echo "$task_result"
export PUBLICATION_HREF=$(echo "$task_result" | jq -r '.created_resources[0]')
