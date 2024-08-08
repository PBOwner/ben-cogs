from redbot.core import commands
from redbot.core.bot import Red
import discord
import typing

def dashboard_page(*args, **kwargs):  # This decorator is required because the cog Dashboard may load after the third party when the bot is started.
    def decorator(func: typing.Callable):
        func.__dashboard_decorator_params__ = (args, kwargs)
        return func
    return decorator

class DashboardIntegration:
    bot: Red

    @commands.Cog.listener()
    async def on_dashboard_cog_add(self, dashboard_cog: commands.Cog) -> None:  # ``on_dashboard_cog_add`` is triggered by the Dashboard cog automatically.
        dashboard_cog.rpc.third_parties_handler.add_third_party(self)  # Add the third party to Dashboard.

    @dashboard_page(name="manage_questions", description="Manage the questions for the Mental Health Buddy application.", methods=("GET", "POST"), is_owner=True)
    async def manage_questions_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_questions_form_")
            question: wtforms.StringField = wtforms.StringField("Question:", validators=[wtforms.validators.InputRequired()])
            action: wtforms.SelectField = wtforms.SelectField("Action:", choices=[("add", "Add"), ("remove", "Remove"), ("clear", "Clear All")])
            index: wtforms.IntegerField = wtforms.IntegerField("Index (for remove action):", validators=[wtforms.validators.Optional()])
            submit: wtforms.SubmitField = wtforms.SubmitField("Update Questions")

        form: Form = Form()
        if form.validate_on_submit():
            question = form.question.data
            action = form.action.data
            index = form.index.data
            async with self.config.guild(guild).questions() as questions:
                if action == "add":
                    questions.append(question)
                    message = "Question added."
                    category = "success"
                elif action == "remove":
                    if 0 < index <= len(questions):
                        removed_question = questions.pop(index - 1)
                        message = f"Removed question: {removed_question}"
                        category = "success"
                    else:
                        message = "Invalid question index."
                        category = "error"
                elif action == "clear":
                    questions.clear()
                    message = "All questions cleared."
                    category = "success"
            return {
                "status": 0,
                "notifications": [{"message": message, "category": category}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }

    @dashboard_page(name="manage_channel", description="Set the application channel.", methods=("GET", "POST"), is_owner=True)
    async def manage_channel_page(self, user: discord.User, guild: discord.Guild, **kwargs) -> typing.Dict[str, typing.Any]:
        import wtforms
        class Form(kwargs["Form"]):
            def __init__(self):
                super().__init__(prefix="manage_channel_form_")
            channel: wtforms.IntegerField = wtforms.IntegerField("Channel ID:", validators=[wtforms.validators.InputRequired(), kwargs["DpyObjectConverter"](discord.TextChannel)])
            submit: wtforms.SubmitField = wtforms.SubmitField("Set Channel")

        form: Form = Form()
        if form.validate_on_submit() and await form.validate_dpy_converters():
            channel = form.channel.data
            await self.config.guild(guild).application_channel.set(channel.id)
            return {
                "status": 0,
                "notifications": [{"message": f"The application channel has been set to {channel.mention}.", "category": "success"}],
                "redirect_url": kwargs["request_url"],
            }

        source = "{{ form|safe }}"

        return {
            "status": 0,
            "web_content": {"source": source, "form": form},
        }
