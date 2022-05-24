FROM ubuntu:20.04
#
# Build stress tool
#
RUN apt-get update && apt-get -y upgrade
RUN apt-get install -y stress-ng

ENV STRESS_CPU=1
ENV STRESS_VM=1
ENV STRESS_VM_BYTES=256M
ENV STRESS_TIMEOUT=30s

CMD stress --cpu ${STRESS_CPU} --vm ${STRESS_VM} --vm-bytes ${STRESS_VM_BYTES} --timeout ${STRESS_TIMEOUT}