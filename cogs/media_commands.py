from urllib.parse import urlsplit

import asyncpg
import voxelbotutils as utils

from cogs.localutils.omdb import get_media_info, get_stream_locations


class MediaCommands(utils.Cog):

    @utils.command()
    async def rate(self, ctx:utils.Context, rating:int, *, media_name:str):
        """
        This is the help text for the rate command.
        """

        # Make sure their rating is valid
        if rating > 5 or rating <= 0:
            return await ctx.send("Please rate this title from 1 to 5")

        # Try and add their rating to the database
        async with self.bot.database() as db:
            try:
                await db(
                    """INSERT INTO user_ratings (user_id, media_title, rating) VALUES ($1, $2, $3)""",
                    ctx.author.id, media_name, rating,
                )
                return await ctx.send("Added rating")
            except asyncpg.UniqueViolationError:
                pass

        # See if they want to update their current rating
        bm = await ctx.send("Would you like to change your rating?")
        await bm.add_reaction("\N{THUMBS UP SIGN}")
        await bm.add_reaction("\N{THUMBS DOWN SIGN}")
        check = lambda r, u: r.message.id == bm.id and u.id == ctx.author.id and str(r.emoji) in ["\N{THUMBS UP SIGN}", "\N{THUMBS DOWN SIGN}"]
        userReaction, _ = await self.bot.wait_for("reaction_add", check=check)
        await bm.delete()

        # Check what reaction they added
        if userReaction.emoji == "\N{THUMBS DOWN SIGN}":
            return await ctx.send("Cancelled rating change!")

        # Change their current rating
        async with self.bot.database() as db:
            await db(
                """UPDATE user_ratings SET rating = $2 WHERE user_id = $1 AND media_title = $3""",
                ctx.author.id, rating, media_name,
            )
        return await ctx.send("Rating succesfully updated!")

    @utils.command()
    async def poster(self, ctx, *, title:str):
        """
        Get the poster for a given movie.
        """

        media_data = get_media_info(title)

        my_embed = utils.Embed(
            title=media_data["Title"],
            description=media_data["Plot"],
            use_random_colour=True,
        )
        my_embed.set_image(
            url=media_data["Poster"]
        )

        await ctx.send(embed=my_embed)

    @utils.command()
    async def watchwhere(self, ctx, location:str, *, title:str):
        """
        Find out where you can watch a given movie.
        """

        where_to_watch = get_stream_locations(title, location)
        urls = where_to_watch['providers']
        description_lines = [f"[{urlsplit(i).hostname}]({i})" for i in urls]

        myEmbed = utils.Embed(
            title=where_to_watch['title'],
            description="\n".join(description_lines),
        )
        myEmbed.set_image(url=where_to_watch['poster'])
        myEmbed.set_footer(text=location)

        await ctx.send(embed=myEmbed)


def setup(bot:utils.Bot):
    x = MediaCommands(bot)
    bot.add_cog(x)
