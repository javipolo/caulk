#!/bin/bash

kind_version=v0.11.1
kind_image=kindest/node:v1.20.7
kind_name=caulk

tmp=$(mktemp -d)
kind=$tmp/kind
export KUBECONFIG=$tmp/kubeconfig

cleanup(){
    pkill -P $$
    kind delete cluster --name=${kind_name}
    rm -fr $tmp
}
#trap cleanup EXIT

# Setup kind
curl -sLo ${kind} https://kind.sigs.k8s.io/dl/${kind_version}/kind-linux-amd64
chmod +x ${kind}
kind create cluster --image=${kind_image} --name=${kind_name} --wait=5m

# Install custom CRDS
curl -sL https://raw.githubusercontent.com/traefik/traefik-helm-chart/master/traefik/crds/middlewares.yaml | kubectl apply -f -
kubectl apply -f helm/crds/middleglue.yaml

kopf run caulk.py --all-namespaces --quiet &

pytest -v
