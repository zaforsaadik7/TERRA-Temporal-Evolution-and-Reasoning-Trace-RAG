# Namespace-closure refinement

R02 adds explicit project-directory membership (excluding only independently
pinned anchor/launcher), complete stdlib namespace excluding global site-packages,
complete base-runtime top-level file membership, and pinned venv configuration
with global sites disabled. Parent before/after and child pre-model checks use it.
Initial33-entry package remains immutable except its four active-source rows
(filesystem, packet, production, packet tests) are superseded by this R02.

The stdlib filesystem preparation's overbroad global-site walk was stopped and
preserved separately. No model/DB/native cohort or actual attempt retry occurred.
