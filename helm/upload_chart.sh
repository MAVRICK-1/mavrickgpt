rm -rf ./tmp
mkdir ./tmp
cd ./tmp
helm package ../mavrick
mkdir mavrick
mv *.tgz ./mavrick
curl https://robusta-charts.storage.googleapis.com/index.yaml > index.yaml
helm repo index --merge index.yaml --url https://robusta-charts.storage.googleapis.com ./mavrick
gsutil rsync -r mavrick gs://robusta-charts
gsutil setmeta -h "Cache-Control:max-age=0" gs://robusta-charts/index.yaml
cd ../
rm -rf ./tmp
