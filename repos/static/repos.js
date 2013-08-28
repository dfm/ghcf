(function () {

  "use strict";

  var ReposApp = Backbone.Router.extend({

    routes: {
      "": "index",
      ":username/:reponame": "repos"
    },

    index: function () {
      console.log("sup foo.");
    },

    repos: function (username, reponame) {
      console.log(username, reponame);
    }

  });

  var Repository = Backbone.Model.extend();
  var RepositoryCollection = Backbone.Collection.extend({
    model: Repository,
    url: function () { return window.API_URL; },
    parse: function (response) { return response.repos; },
  });

  $(function () {
    window.app = new ReposApp();
    Backbone.history.start({pushState: true});
    var c = new RepositoryCollection();
    c.fetch({repo: "dfm/emcee"});
    console.log(c);
  });

})();
