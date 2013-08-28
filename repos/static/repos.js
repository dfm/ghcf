(function () {

  "use strict";

  var ReposApp = Backbone.Router.extend({
    initialize: function () {
      this.view = new ReposView({model: new Repos(), el: "#recommendations"});
      this.view.$el.hide();
      var this_ = this;
      $("#repoform").on("submit", function () {
        this_.navigate($("#repoinput").val(), {trigger: true});
        return false;
      });
    },
    routes: {
      "": "index",
      ":fail": "fail",
      ":username/:reponame": "repos"
    },
    index: function () {
      $("#errorblock").hide();
      $("#invalidblock").hide();
    },
    fail: function () {
      $("#errorblock").hide();
      $("#invalidblock").show();
    },
    repos: function (username, reponame) {
      var fullname = username+"/"+reponame;
      $("#repoinput").val(fullname);
      $("#errorblock").hide();
      $("#invalidblock").hide();

      $("#loading").show();
      this.view.$el.hide();

      this.view.model.fetch({data: {repo: fullname}});
    }
  });

  //
  // Models
  //
  var Repo = Backbone.Model.extend();
  var Repos = Backbone.Collection.extend({
    model: Repo,
    url: function () { return window.API_URL; },
    parse: function (response) { return response.repos; },
    comparator: function (repo) { return -repo.get("score"); }
  });

  //
  // Views
  //
  var ReposView = Backbone.View.extend({
    initialize: function() {
      this.listenTo(this.model, "sync", this.render);
    },
    template: _.template($("#repo-template").html()),
    render: function () {
      this.$el.find(".repo").remove();
      var this_ = this, template = this.template;
      $("#loading").hide();
      if (this.model.models.length == 0) {
        this.$el.hide();
        $("#errorblock").show();
        return this;
      }
      this.model.models.map(function (repo) {
        var el = $(template(repo.attributes)),
            url = repo.get("name");
        el.find(".more").on("click", function () {
          app.navigate(url, {trigger: true});
          return false;
        });
        this_.$el.append(el);
      });
      this.$el.show();
      return this;
    }
  });

  $(function () {
    window.app = new ReposApp();
    Backbone.history.start({pushState: true});
  });

})();
