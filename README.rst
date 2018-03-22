Learn Deep NRP
============================

Status
---------

An older more stable version of this codebase has been deployed for Learn Deep.  Some work will continue to go on there, as needed by the Learn Deep organization.  You can see it here: http://nrp.webfactional.com/.

This version (latest Django version, graphql api in progress) will be used for the backend of the new version for Learn Deep. This version will get the new work being added to the older version when it is complete.  That will be before the end of the class sprint 0.

API
------

There is a new API being developed on this codebae to support the graphql based UI.  This is being developed in the upstream version from which this repo was first forked.

To sync your version with the upstream version:  Do a fetch, and always merge the api-extensions branch, do NOT merge master.  (Master has a lot of features and changes that LearnDeep doesn't want, and in fact doesn't have the api yet.  We will maintain the api-extensions branch there as a branch that has the most up-to-date api code.)

History and connections
----------------------------

This was forked from Freedom Coop's OCP, which was forked from Mikorizal's NRP.

We mean Accounting in a large sense.  We are developing something analogous to an ERP system for value networks.
Might call it NRP for Network Resource Planning or OCP for Open Collaborative Platform.

More info abount NRP accounting: `Slide deck <https://docs.google.com/presentation/d/1JEPsxJOjEMHNhvIGLXzcvovrpXqpoY75YaPHDKI0t9w/pub?start=false&loop=false&delayms=3000>`_.

See `docs <https://github.com/FreedomCoop/valuenetwork/tree/master/docs>`_ for developer installation instructions.

The graphql API is being developed in conjunction with the React UI in the rea-app repository here.  It uses the `ValueFlows <https://valueflo.ws>`_ vocabulary.

