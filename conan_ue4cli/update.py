from .RecipeCache import RecipeCache

def update(manager, argv):
	
	# Update our recipe cache
	print('Updating the recipe cache...')
	RecipeCache.updateCache()
	print('\nRecipe cache updated.')
