do-pod-dns-controller
=====================

What is it?
-----------

This is a simple controller written in Python that will configure a
DNS A record on DigitalOcean with the external IP of each node that
annotated pods are running on. The purpose is to allow exposing
services via hostPort for situations such as UDP services where a
LoadBalancer service won't work, and where a service with externalIPs
isn't desirable due to performance or because it loses the client's
IP.

This will probably be most useful with ingress controller pods, but it
can be used with any pod that exposes services via hostPorts.


How does it work?
-----------------

The controller lists your nodes and pods every 10 seconds. It looks
for pods with the annotation
`do-pod-dns-controller.literati.org/hostname`. It collects the
external IPs of each node that a pod with a given hostname annotation
is running on, then makes it so that the given hostname has A records
for exactly those external IPs, deleting any extraneous A records. It
will not touch any other records.


How do I use it?
----------------

Use a manifest similar to the one under examples. Generate a
DigitalOcean token and set that in a secret that ends up as
DIGITALOCEAN_TOKEN in the controller's environment. Make sure you've
already set up each domain name you want to use in DigitalOcean's
domain settings, then add `--domain=<domain>` to the controller's
args, for each domain. Annotate each pod (via
spec.template.metadata.annotations in Deployments, DaemonSets, etc)
with the key `do-pod-dns-controller.literati.org/hostname` and the
FQDN you want to set the DNS for, for example:

```
apiVersion: apps/v1
kind: Deployment
...
spec:
  template:
    metadata:
	  annotations:
	    do-pod-dns-controller.literati.org/hostname: www.example.com
...
```

Then watch the logs for the controller pod. You should see logs
indicating that it's configured DNS, or an error telling you what went
wrong. You can add `--log-level=debug` to the args to get more
logging.


Code of conduct
---------------

Any interactions with the community relating to this software are
governed by the [code of conduct](code_of_conduct.md).
